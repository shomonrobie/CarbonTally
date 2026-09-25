# CT-PO-P17-L — Governed Capability Truth Surface

**Task ID:** `P17-L-20260926-CAPABILITY-TRUTH-SURFACE`
**Type:** IMPLEMENTATION + REAL-POSTGRESQL VERIFICATION
**Date:** 2026-09-26
**Repository:** `/home/shomonrobie/ct_93d5cdd`
**Branch:** `p8-release-reconciled`

---

## 1. Task identity

### 1.1 What this task had to do

`P17-DECISION-03 §18.1` Tier 2 item 7 and §20.3 defined `P17-K`: author the
governed `disclosure_requirement_versions` catalogue rows and add the `§18.3`
gates `AG-1`…`AG-8` as automated tests. `P17-K` did that, and recorded as an
explicit non-claim that the *rendering* branches of `AG-3`…`AG-8` were
**PENDING** because **no surface existed** (`P17-K` report §15, `L-6`).

`P17-L` is the bridge the contract names next:

```text
GOVERNED CAPABILITY CATALOGUE        (P17-K — persisted, verified)
        ↓
CANONICAL READ / PROJECTION          (this task)
        ↓
CUSTOMER / INVESTOR TRUTH SURFACE    (this task)
```

### 1.2 What this task must not do

* **No second capability model, applicability model or status vocabulary**
  (`§4`, `F-1`, `F-2`). One source of truth only: `disclosure_requirement_versions`
  plus the existing governed Disclosure projection/domain logic.
* **No customer-facing category applicability.** The surface answers *"what does
  CarbonTally currently support?"*, never *"which Scope 3 categories apply to
  this customer?"* (`PO-3`).
* **No new enum / status column / coverage field**; no `applicability_status`,
  `NO_DATA_YET`, `EXCLUDED_WITH_REASON`, or `architecture_status` rendered as a
  customer/investor status.
* **No marketing artefacts** (`§21`): no landing page, sales deck, FAQ or
  investor deck was edited.
* **No absorption of `P17-J`** (`§20`). Scope 2 end-to-end acceptance remains a
  separate gate and is not claimed here.
* **No promotion.** Nothing was applied to the demo, QA or production database.

### 1.3 What "verified" means in this report

The final section (§25) separates the terms explicitly. In summary:

| Term | Meaning here |
|---|---|
| **IMPLEMENTED** | code exists in the working tree |
| **PERSISTED** | a governed row/constraint exists in a real database |
| **READABLE** | the surface returns the projection to an authenticated caller |
| **E2E VERIFIED** | the customer/investor surfaces render that payload |
| **REAL-PG VERIFIED** | asserted against a real, migrated PostgreSQL database |
| **INDEPENDENTLY VERIFIED** | checked by an agent/party other than the implementer — **NOT CLAIMED** |
| **ACCEPTED** | a PO/investor acceptance decision — **NOT CLAIMED** |
| **PRODUCTION READY** | deployed and operating under the deployment gate — **NOT CLAIMED** |

---

## 2. Baseline

| Item | Expected | Observed | Result |
|---|---|---|---|
| `HEAD` | `3f3dfa415abc8f8d0767ad4f5339a2cefc9e1e12` | `3f3dfa415abc8f8d0767ad4f5339a2cefc9e1e12` | **MATCH** |
| Branch | `p8-release-reconciled` | `p8-release-reconciled` | **MATCH** |
| `git log -6` | ends `3f3dfa4` (the P17-K commit set) | `3f3dfa4`, `a98315f`, `9ae275b`, `ba19ccd`, `4f8853b`, `28ff2c0` | **MATCH** |
| Working tree | pre-existing `.gitignore` modification + pre-existing untracked files | unchanged | **PRESERVED, UNSTAGED** |
| Distance from `origin` | 192 commits ahead of `origin/p8-release-reconciled` (`93d5cdd`) | 192 ahead | **MATCH** |

Artifacts re-verified present before any change:

* `docs/architecture/CT-PO-P17-K-GOVERNED-CAPABILITY-CATALOGUE-RUNTIME-DIMENSIONS-20260926.md` (1098 lines);
* `supabase/migrations/20261020000000_p17k_governed_capability_catalogue.sql`;
* `backend/tests/unit/data/test_p17k_governed_capability_catalogue.py`;
* `backend/tests/integration/test_p17k_governed_capability_catalogue_runtime.py`.

`git status --porcelain` was recorded before and after every step. The
pre-existing `.gitignore` modification and the pre-existing untracked files were
**not** modified, staged or committed.

---

## 3. Sources

Read before writing any code (via Hindsight recall, the repository, and the live
database):

| Source | Used for |
|---|---|
| `CT-PO-P17-DECISION-03-…-20250926.md` | §5.3 `M-1`, §5.5, `M-2`…`M-6`; §6.3 PO-9; §7 product capability model; §8 customer truth model; §9 investor truth model; §10.3 `SC-4`; §11.1–§11.3 matrix + rollup; §12 lifecycles; §13 Axis A vs Axis B (`IV-1`…`IV-6`); §14.1–§14.4 (`CT-1`…`CT-4`, `IN-1`…`IN-4`, `CS-1`…`CS-5`); §18.1–§18.4; §19.1–§19.4; §20.2–§20.3 |
| `CT-PO-P17-DECISION-01`, `-02` | the four truth levels (L1–L4); the applicability boundary; the `PO-3` antecedents |
| `CT-PO-P17-K-…-20260926.md` | the catalogue's shape and provenance; the pending `AG-3`…`AG-8` rendering branches; `L-1`…`L-6`; `P17K-F1`/`P17K-F2` |
| `P17-PRODUCT-01 — … Product Specification.md` | the product/evidence framing of the capability claims |
| `backend/domain/disclosure.py` | the governed constants: `CARBONTALLY_CAPABILITIES` (7), `REQUIREMENT_CLASSES` (8), `SCOPE2_METHODS`, `IDENTIFIER_STATUSES`, `APPLICABILITY_STATUSES`, `UNRESOLVED_IDENTIFIER` |
| `backend/domain/disclosure_projection.py` | `derive_effective_class` (precedence applicability → capability → requirement class), `UNSUPPORTED_CAPABILITIES`, `UNSUPPORTED_REQUIREMENT_CLASSES` |
| `backend/domain/scope3.py`, `scope3_contracts.py` | the Axis-A `architecture_status` tokens and the refusal principle — confirmed **not** to be a claim source for this surface |
| `backend/data/disclosure.py` | the existing catalogue read model (`DisclosureCatalogRepository`) |
| `backend/api/v3_disclosure.py` | the existing governed Disclosure API surface (extended, not duplicated) |
| `frontend/src/v3/**` | D21 primitives (`Card`, `Badge`, `Alert`, `Icon`, `StateViews`), the `App.js` routing conventions, the D18 `V3Layout` navigation model, the `api.js` fetch wrapper |
| `AGENTS.md` | §5–§7, §13, §25, §44–§46, §55/§55.1, §66, §71–§74, §76 |

**Terminology was taken from those documents verbatim.** No new governed token
was introduced anywhere in this task.

---

## 4. Existing capability projection

### 4.1 What already existed (re-verified, not assumed)

| Layer | Artifact | State at baseline |
|---|---|---|
| Governed vocabulary | `domain.disclosure.CARBONTALLY_CAPABILITIES` | 7 values; EQUAL to the DB CHECK constraint (P17-K `AG-1`) |
| Requirement classes | `domain.disclosure.REQUIREMENT_CLASSES` | 8 values |
| Outcome engine | `domain.disclosure_projection.derive_effective_class` | precedence **applicability → capability → requirement class**; `NOT_APPLICABLE_TO_PRODUCT` derives to `NOT_SUPPORTED`, never to `NOT_APPLICABLE` |
| Catalogue rows | `disclosure_requirement_versions` | 18 rows for the evidenced GHG Protocol version (P17-K), **not** promoted |
| Catalogue read model | `DisclosureCatalogRepository.list_requirements` | selected 11 columns — **no** `description`, `source_locator`, `authoritative_text_ref`, `source_tier` |
| Axis-A tokens | `domain/scope3.py`, `scope3_contracts.py`, `api/v3_scope3.py:230` | internal only; `architecture_status` crosses an internal API |

### 4.2 What was missing

`P17-K §15`/`L-6`: the *rendering* branches of `AG-3`, `AG-4`, `AG-5`, `AG-7`
and `AG-8` were **PENDING** because there was no surface, no canonical
projection and no read model that carried the provenance a capability claim
needs.

### 4.3 The canonical projection (new)

`backend/domain/capability_catalogue.py` — pure, no I/O, no pool, no tenant, no
clock. It declares **no** vocabulary of its own: every governed token it emits
is imported from `domain.disclosure` / `domain.disclosure_projection`. It is a
projection, **not** a second capability configuration file (`§5`, `F-2`).

| Function | Purpose |
|---|---|
| `dimensions_for_requirement_code(code)` | derives `{scope, scope2_method, scope3_category}` from the catalogue identity (`GP-S1`, `GP-S2-LB`, `GP-S2-MB`, `GP-S3-CAT-NN`); an unrecognised code **raises** rather than inventing a dimension |
| `capability_explanation(value)` | the truthful, non-upgrading explanation per governed value, taken from the frozen `M-6`/`§5.5`/`§12.2` wording |
| `capability_glossary()` | the 7 governed values with their meaning, in governed order — so no consumer hardcodes capability semantics |
| `project_requirement(row)` | one persisted row → its governed surface shape |
| `scope3_capability_rollup(rows)` | the four-way split, recomputed from the rows; a value outside the four buckets **raises** |
| `project_capability_catalogue(...)` | the whole projection + the three render guards |
| `assert_no_axis_a_status_token(payload)` | `AG-3` guard, word-boundary matched |
| `assert_no_placeholder_or_figure(payload)` | `AG-4` guard |
| `assert_no_forbidden_field(payload)` | `F-1`/`F-2`/`F-8`/`AG-7` field guard |
| `capability_for_scope3/scope2(...)` | lookup helpers for consumers and tests |
| `is_governed_requirement_code(code)` | the **single** definition of the governed requirement-identity grammar (implemented in terms of `dimensions_for_requirement_code`), used by the surface to select the governed catalogue version |


### 4.4 The projection payload (shape)

```text
surface                    "CAPABILITY_TRUTH"
framework                  {code, name, publisher, kind}
framework_version          {version_label, status, source_tier, source_url,
                            authoritative_source_date}
capability_vocabulary      the 7 governed values, quoted from the code constant
capability_glossary        [{value, explanation}] x 7
requirements               [ 18 x §4.5 ]
scope3_capability_rollup   {SUPPORTED, PARTIALLY_SUPPORTED, FUTURE, MISSING_CAPABILITY}
scope3_rollup_basis        prose: derived, four-way, never a total/coverage
result_presence_note       prose: capability (not) result (§8)
```

### 4.5 Per-requirement fields (`§7` minimum, all satisfied)

`requirement_code`, `requirement_name`, `framework_code`,
`framework_version_label`, `scope`, `scope2_method`, `scope3_category`,
`carbontally_capability`, `capability_explanation`, `requirement_class`,
`requirement_class_expression`, `supported`, `provenance{source_locator,
authoritative_text_ref, source_tier, official_identifier, identifier_status}`,
`capability_detail` (the catalogue's own bounded-scope / named-prerequisite
text, verbatim), `result_presence` (**always `null`** — see §8).

### 4.6 Two decisions worth stating explicitly

* **`requirement_class_expression`** is `M-1`'s third column — *"the governed
  requirement class when a requirement is in play"* — produced by the **existing**
  `derive_effective_class` with the neutral posture `APPLIES` that P17-K's own
  `AG-2` test established. It is a **requirement-class outcome, never an
  applicability outcome**: no applicability status is ever supplied, so
  `NOT_APPLICABLE` is structurally unreachable (test-locked).
* **`supported`** is `carbontally_capability not in UNSUPPORTED_CAPABILITIES`
  (the governed engine's own notion of "not producible"). Therefore
  `PARTIALLY_SUPPORTED` is **bounded support, not an upgrade** (`IV-5`), and the
  two input-limited values (`STRUCTURED_INPUT_REQUIRED`,
  `EXTERNAL_INPUT_REQUIRED`) remain *expected* (`§12.2(2)`) rather than being
  collapsed into "unsupported". A coarse boolean was deliberately avoided
  because it would flatten the four-way split.

---

## 5. Read-model / API implementation

### 5.1 The read model (additive)

`backend/data/disclosure.py`, on the **existing** `DisclosureCatalogRepository`:

* new constant `_CAPABILITY_REQUIREMENT_COLUMNS` — a superset of
  `_REQUIREMENT_COLUMNS` that also selects `description`, `source_locator`,
  `authoritative_text_ref`, `source_tier` and the framework/version context;
* new method `capability_catalogue_candidates()` — every framework version that
  carries requirement rows, with its requirement codes and its framework code;
* new method `list_capability_catalogue_requirements(framework_version_id)`.

**Version scoping is the correction this task had to make** (§18.1.1). The first
revision filtered on the framework *code*, so any other version of the same
framework merged into the claim and the projection then — correctly — refused the
whole statement. The surface now selects the governed catalogue **by rule**
(the first candidate carrying at least one governed requirement identity) and
reads requirements by `framework_version_id`. The identity grammar stays defined
in exactly one place (`domain.capability_catalogue`), via the new
`is_governed_requirement_code()` helper.

Deliberately **additive**: `_REQUIREMENT_COLUMNS` and `list_requirements` are
byte-unchanged, so every pre-existing consumer keeps its exact row shape.

Both queries join **only** the three governed catalogue tables
(`disclosure_requirement_versions`, `disclosure_framework_versions`,
`disclosure_frameworks`) — no tenant table, no `organization_id` predicate, no
`current_setting`, no `auth.uid` (`SEC-1`, `SEC-3`, `AG-5`).

### 5.2 The endpoint (one route, extended module)

`GET /api/v3/capabilities`, added to the **existing** governed Disclosure module
`backend/api/v3_disclosure.py` (prefix `/api/v3`) — the module that already owns
the disclosure catalogue read surfaces. No second endpoint family, no new router
module, no duplicate read model (`§16`).

| Property | Implementation |
|---|---|
| Authentication | `Depends(get_current_user)` — authenticated, and **nothing more**: capability is product truth, so no organisation membership is required |
| Tenant context | **None accepted.** The route declares **no parameters at all** (asserted from the generated OpenAPI schema), reads none, and answers identically for every caller |
| Server authority | The payload is derived from persisted rows through the existing governed engine; nothing is hardcoded in the route |
| Fail-closed | An unprovisioned framework, a missing version row, or a row outside the governed vocabulary ⇒ **503**, a friendly message, and **no claim** (`CS-3`, `IV-4`, `AGENTS.md §46`) |
| Read-only | One `GET`, no write verb (asserted) |

### 5.3 Why "authenticated but tenant-free" is the right posture

`DECISION-03 §19.2 SEC-1` states that an endpoint serving this surface *"must be
safe to serve **without** any tenant context — i.e. it must be derived from
governed catalogue and product-level facts only"*, and `§16` requires
authenticated access. Requiring organisation membership instead would couple
product truth to tenancy and would deny the internal/PE/consultant actors who
also need to know what the product supports — without adding any security, since
the payload contains no tenant data. `SEC-2` (no service-role shortcut) is
respected: the route uses the same authenticated dependency every other V3
surface uses, and the fixture is never reached.


---

## 6. Customer surface

**Route:** `/capabilities` — `ProtectedRoute` → `RoleRoute requireOrg` →
`V3Layout` → `CapabilitiesPage` (`frontend/src/v3/capabilities/CapabilitiesPage.jsx`).

The page is inside the org-scoped shell (the customer is *in* their workspace),
but it makes **no tenant-scoped request**: its only call is
`getCapabilityCatalogue()`. That is the point — the customer can now answer
`§8`'s first question (*"what can CarbonTally do for me?"*) from governed
product truth, while their **own** answers live where their own data lives:

> Your own calculated results live on your **Emissions** and **Reports** pages.
> This page never states a result for your organisation, so a requirement listed
> here without a result of yours is not an unsupported requirement.

It renders the shared `CapabilityTruthSurface` with `audience="customer"`, plus a
single cross-link to the product presentation. It uses the D21 primitives
(`Alert`, `Badge`, `Icon`, `LoadingState`, `ErrorState`) and a page-scoped
stylesheet built on the `ct-*` tokens (the `reports/reports.css` precedent).

**Navigation:** exactly **one** added entry in the existing D18 `CUSTOMER_LINKS`
model — `{ to: '/capabilities', label: 'Capabilities', icon: 'list' }`. This
follows the precedent already set for the I6 Insight entry (*"one added entry in
the existing D18 customer model, not a navigation redesign"*). No navigation
model was redesigned.

**Empty/error/loading states** (`AGENTS.md §47`, `§48`): a loading state, a
bounded retryable error state, and — on failure — **no claim is shown at all**
(`CS-3`).

---

## 7. Investor surface

**Route:** `/capabilities/product` — `ProtectedRoute` → `V3Layout` →
`InvestorCapabilityPage` (`frontend/src/v3/capabilities/InvestorCapabilityPage.jsx`).

Deliberately **not** `RoleRoute requireOrg`: it resolves **no organisation** and
issues **no tenant query**. The page does not even import the organisation
resolver — a static assertion in the frontend suite (`ag_5 the product surface
opens no tenant query path`) and in the backend suite
(`test_ag_6_both_surfaces_render_from_this_single_payload`) fails if it ever
does.

It renders the **same** `CapabilityTruthSurface` with `audience="investor"`, so:

* every governed value is the same value the customer sees (`CS-2`, `AG-6`);
* the customer-only "where your own results live" paragraph is **omitted**;
* nothing tenant-identifying exists to omit in the first place (`CS-1`, `§19.4`
  row 8);
* the footer states plainly that this is a product-level statement containing no
  customer/organisation information (`IN-1`).

It may display exactly what `§14` permits: governed product capabilities, the
capability rollup, supported Scope 2 methods, Scope 3 category capability state,
methodology/evidence concepts only where actually supported, and explicit
capability limitations. It displays **none** of the prohibited items: no
customer information, no tenant identifier, no emissions figure, no fabricated
evidence or supplier data, no unsupported category claim, no applicability or
materiality claim, no coverage percentage, no "100% Scope 3 coverage" and no
internal development status (`§9.4` items 1–10).

---

## 8. Scope 2 capability surface

`Scope2Panel` renders the Scope 2 requirements **by governed method**, from the
projection (`scope2_method` ∈ `SCOPE2_METHODS`), never merged and never summed:

| Persisted requirement | Governed method | `carbontally_capability` | `requirement_class_expression` |
|---|---|---|---|
| `GP-S2-LB` | `LOCATION_BASED` | `SUPPORTED` | `REQUIRED` |
| `GP-S2-MB` | `MARKET_BASED` | `MISSING_CAPABILITY` | `NOT_SUPPORTED` |

`SC-4` is enforced as a test, not a convention:
`test_sc_4_market_based_scope2_is_not_claimed_supported` asserts that the
market-based requirement is neither `SUPPORTED` nor `PARTIALLY_SUPPORTED`, and
the runtime suite asserts the same against the **persisted** row.

The panel states: *"The method is part of a result's identity and is never
inferred… a method is never implied from another method's support."*

**`P17-J` is not absorbed.** No Scope 2 end-to-end acceptance is claimed
anywhere in this task or on this surface; the panel renders **capability**, not a
verified Scope 2 result path (`§20`).


---

## 9. Scope 3 1–15 surface

`Scope3Table` renders all 15 categories, in category order, from the projection.
It carries **the exact P17-K `M-1` image**, never silently upgraded (`S3-2`):

| # | Requirement code | Governed capability | `requirement_class_expression` |
|---|---|---|---|
| 1 | `GP-S3-CAT-01` | `PARTIALLY_SUPPORTED` | `CONDITIONAL` |
| 2 | `GP-S3-CAT-02` | `MISSING_CAPABILITY` | `NOT_SUPPORTED` |
| 3 | `GP-S3-CAT-03` | `SUPPORTED` | `CONDITIONAL` |
| 4 | `GP-S3-CAT-04` | `SUPPORTED` | `CONDITIONAL` |
| 5 | `GP-S3-CAT-05` | `SUPPORTED` | `CONDITIONAL` |
| 6 | `GP-S3-CAT-06` | `SUPPORTED` | `CONDITIONAL` |
| 7 | `GP-S3-CAT-07` | `PARTIALLY_SUPPORTED` | `CONDITIONAL` |
| 8 | `GP-S3-CAT-08` | `PARTIALLY_SUPPORTED` | `CONDITIONAL` |
| 9 | `GP-S3-CAT-09` | `PARTIALLY_SUPPORTED` | `CONDITIONAL` |
| 10 | `GP-S3-CAT-10` | `MISSING_CAPABILITY` | `NOT_SUPPORTED` |
| 11 | `GP-S3-CAT-11` | `FUTURE` | `FUTURE` |
| 12 | `GP-S3-CAT-12` | `PARTIALLY_SUPPORTED` | `CONDITIONAL` |
| 13 | `GP-S3-CAT-13` | `PARTIALLY_SUPPORTED` | `CONDITIONAL` |
| 14 | `GP-S3-CAT-14` | `FUTURE` | `FUTURE` |
| 15 | `GP-S3-CAT-15` | `FUTURE` | `FUTURE` |

Each row shows: the governed value **verbatim** (`IV-2` — the value *is* the
claim), the payload's explanation for that value, the catalogue's own
bounded-scope / named-prerequisite text (`capability_detail`, verbatim — this is
how `M-6`'s *"plus an explicit statement of what is outside scope"* and `IT-3`'s
*"the prerequisite is named"* are satisfied without inventing anything), the
provenance, and the explicit absence line *"No result is stated here for any
organisation."*

**The surface can distinguish `SUPPORTED` / `PARTIALLY_SUPPORTED` / `FUTURE` /
`MISSING_CAPABILITY` only because the governed projection says so.** The
vocabulary and every explanation arrive from the API (`capability_vocabulary`,
`capability_glossary`); a static test asserts that `GP-S3-CAT-` and any
category→status table are **absent from the frontend source**. No internal
`architecture_status` is exposed anywhere (`F-3`).

An unrecognised value (should one ever be persisted) is still rendered
**verbatim**, with a neutral presentation, rather than hidden — `IV-4`: say less,
never something invented.

---

## 10. Four-way rollup

`CapabilityRollup` renders `scope3_capability_rollup` exactly as the projection
produced it:

| Governed value | Count |
|---|---|
| `SUPPORTED` | 4 |
| `PARTIALLY_SUPPORTED` | 6 |
| `FUTURE` | 3 |
| `MISSING_CAPABILITY` | 2 |

Properties, each one a test:

* **derived from persisted catalogue rows** — `scope3_capability_rollup()` reads
  the rows; the runtime suite additionally re-derives the same split with a
  `GROUP BY` in SQL and asserts equality;
* **never hardcoded** — the frontend renders `Object.entries(rollup)`; a static
  assertion forbids a category table in the frontend;
* **never calculated from tenant data** — nothing tenant-scoped is read at all
  (§12/§13);
* **never a total or a coverage score** — there is no key whose name contains
  `coverage`, `total`, `percentage`, `score`, `materiality` or `assurance`
  (`assert_no_forbidden_field`, asserted in unit, API and runtime suites);
* **never implies applicability and never implies emissions completeness** —
  `AG-7` `S3-1` semantics are preserved, and the basis text says so;
* the frontend suite asserts the rollup element contains **exactly four** items
  and no `n/15` or `%` expression anywhere on the page.

---

## 11. Provenance

Every capability claim retains provenance (`§12`, `AG-8`):

| Field | Source column | Rendered |
|---|---|---|
| `source_locator` | `disclosure_requirement_versions.source_locator` | yes, per requirement |
| `authoritative_text_ref` | `…authoritative_text_ref` | yes (payload; shown in detail views) |
| `source_tier` | `…source_tier` | yes ("Source tier 1") |
| `official_identifier` | `…official_identifier` | yes (null when unresolved) |
| `identifier_status` | `…identifier_status` | yes |

`P17-K` recorded `UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION` for the catalogue
because the authoritative Chapter 9 required-information lists are not machine-
readable. **That truth is preserved, not smoothed**: when the status is not
`RESOLVED`, the surface renders

> Authoritative identifier unresolved: no official identifier is asserted for
> this requirement (authoritative-source limitation).

and the runtime suite asserts the marker in the payload **equals** the value
persisted in `identifier_status` for every one of the 18 rows, and that
`official_identifier IS NULL` wherever the status is unresolved (so no identifier
was invented). No official identifier, source date, URL or methodology claim was
invented anywhere in this task.


---

## 12. Tenant / security

### 12.1 The capability catalogue is product-level truth

| Property | How it is enforced | How it is verified |
|---|---|---|
| No tenant column | the catalogue tables have none (`information_schema.columns`) | runtime: `test_the_catalogue_tables_carry_no_tenant_column` |
| No FK path to a tenant table | `information_schema` FK walk over the 3 catalogue tables | runtime: `test_no_foreign_key_leads_from_the_catalogue_to_a_tenant_table` |
| No tenant predicate in the query | the shipped SQL joins catalogue tables only | API: AST audit of the executed SQL literals + the selected column list; runtime: identical results under two JWT contexts |
| No tenant parameter accepted | the route declares **no parameters** | API: OpenAPI schema assertion (`declared == set()`) |
| No tenant data returned | no tenant token appears in the payload | API + runtime: 8-token scan over the serialised payload |
| No tenant-table query issued | a query logger over a real connection captures every statement | runtime: `test_no_tenant_query_is_issued_by_the_read_model` |

`SEC-3` is honoured the hard way: **the query path is checked, not only the
rendered output.**

### 12.2 Same capability response under two authorised tenant contexts

`§13` requires a test proving it, and there are three:

1. `test_two_tenant_contexts_see_identical_capability_truth` — a **single-connection**
   pool with `request.jwt.claims` set to two different tenant subjects. Any tenant
   predicate would produce different reads; they are byte-identical.
2. `test_the_http_surface_is_byte_identical_under_two_identities` — two **real**
   `organizations` rows are created, two distinct authenticated actors call the
   real HTTP route on the real database, and `response_a.content ==
   response_b.content`; neither organisation id appears in either response.
3. `test_the_product_surface_answers_without_any_tenant_context` — an
   authenticated **non-org-member** (internal staff) is admitted and receives the
   same 18 requirements and the same rollup (`§19.2 SEC-1`: the endpoint is safe
   to serve with no tenant at all).

### 12.3 `§19.4` rows 8 and 9

| # | Boundary | Expected | Verification |
|---|---|---|---|
| **8** | Investor surface → any tenant data | **DENY / IMPOSSIBLE** | no tenant column, no FK path, no tenant predicate, no tenant parameter, no tenant token in the payload, no tenant query on the wire, and byte-identical payloads across two real tenants |
| **9** | Any non-internal surface → Axis-A vocabulary | **ABSENT** | the payload contains no `PARTIAL`/`DEFERRED`/`NOT_IMPLEMENTED` (word-boundary matched) and no `architecture_status`; the persisted row text (title/description) is asserted clean too, so a surface cannot leak an internal status by copying prose |

### 12.4 No RLS, policy or grant was changed

`P17-L` adds **no** migration, table, column, enum, CHECK, index, policy or
grant. The catalogue's existing `SELECT TO authenticated USING (true)` policies
are untouched and unneeded by this surface (the route reads through the
process-level service pool with application-level authentication, exactly as the
other governed disclosure reads do).

### 12.5 Production safety

* **Production contacted: NO.** No production host, endpoint or database was
  reached.
* **`carbontally_demo_local`: read-only** (two `SELECT count(*)`s) and
  **verified unmodified** (`disclosure_requirement_versions` = 0,
  `disclosure_framework_versions` = 0, `organizations` = 4 before and after).
* **`carbontally_test`: not touched.** The suite asserts its own target is not
  that database.
* **`ct_p17k_20260926` (P17-K's evidence clone): used read-only during P17-L.**
  It served as the `TEMPLATE` for this task's clone (read-only for the source),
  and P17-L's integration target was always `ct_p17l_surface_20260926`. It was
  **later** used as the *comparison target* for the pre-existing-failure
  reproduction in §20.2/§20.3 — and those suites perform the standard destructive
  integration setup on their target, so it now carries their residue
  (55 | 26 totals). **The governed catalogue on the evidenced version is intact
  there (18 rows)**, verified after the fact. It is a disposable `ct_*` clone —
  not the demo database, not `carbontally_test`, not production.
* **F-046-1** is restated in the integration module docstring and exercised as a
  test (§18 step 9).
* No secret, credential, JWT, signed URL or connection string appears in this
  report or in any committed file.


---

## 13. `AG-3` — no Axis-A token is rendered

**Gate:** *"No Axis-A token is rendered on any non-internal surface — string scan
for `PARTIAL`, `DEFERRED`, `NOT_IMPLEMENTED` used as a status."* (`IV-1`, `F-3`)

**P17-L status: the rendering branch is now CLOSED.**

| Layer | Verification |
|---|---|
| Persisted rows | `test_ag_3_no_axis_a_token_exists_in_the_persisted_catalogue` — a case-insensitive PostgreSQL regex over `requirement_code`, `title` and `description`; 0 offenders |
| Projection | `test_ag_3_no_axis_a_token_is_renderable` + `assert_no_axis_a_status_token` runs **inside** `project_capability_catalogue`, so a projection cannot return a token even if a caller forgets the guard |
| Guard correctness | `test_ag_3_the_scan_distinguishes_a_governed_value_from_the_internal_token` — `PARTIALLY_SUPPORTED` is a **governed** value and is NOT flagged; `PARTIAL`, `DEFERRED`, `NOT_IMPLEMENTED` are |
| Guard fires | `test_ag_3_the_guard_refuses_an_injected_token` (4 parametrisations, incl. lowercase `deferred`) |
| HTTP payload | `test_ag_3_no_axis_a_token_is_renderable` on the real response, word-boundary matched |
| Rendered DOM | `ag_3 no Axis-A token is rendered on either surface` on **both** customer and product surfaces, plus `architecture_status` |
| Field names | `assert_no_forbidden_field` rejects any field name containing `architecture_status` |

**A nuance worth recording.** A naive substring scan for `PARTIAL` would "fail" on
the legitimate governed value `PARTIALLY_SUPPORTED`, and a naive scan for
`DEFERRED` would "fail" on honest prose. The guard therefore matches on **word
boundaries** (`\b(PARTIAL|DEFERRED|NOT_IMPLEMENTED)\b`, case-insensitive), and
the `M-6` wording for the governed `FUTURE` value was written to avoid the
substring entirely (*"has not yet delivered … pending the named decision or
prerequisite"*). `AG-3` is satisfied by **not producing** internal vocabulary —
never by censoring a governed value.

---

## 14. `AG-4` — no placeholder and no fabricated figure

**Gate:** *"No `0`, `0 tCO₂e`, `N/A`, `—`, `not applicable`, `excluded`,
`coming soon` appears for a non-produced item — negative tests, one per state
(both surfaces)."* (`F-6`, `S3-5`, `§9.4` item 7)

**P17-L status: the rendering branch is now CLOSED.**

| Check | Verification |
|---|---|
| Placeholder tokens | `FORBIDDEN_PLACEHOLDER_PATTERN` = `N/A`, `not applicable`, `non-applicable`, `excluded`, `coming soon`, `TBC`, `TBD`, `0 <unit>`; the API suite parametrises **6** placeholder tokens over the real payload, and the frontend suite scans the rendered DOM for all of them |
| Fabricated figures | `EMISSIONS_FIGURE_PATTERN` — no `\d+ (kg|t|tonnes|tCO2e)` anywhere; asserted on the payload (unit + API + runtime) and on the rendered DOM |
| Per-state absence | every requirement carries an **explicit governed capability value** — never a placeholder, never a blank; and `result_presence` is `None` for all 18 |
| Never zero | `test_ag_4_a_requirement_with_no_result_is_never_zero` asserts `result_presence is None` and `!= 0` for every requirement; the rendered row asserts the absence *statement* instead |
| `NOT_APPLICABLE_TO_PRODUCT` | proven not to be the phrase "not applicable" (`test_the_governed_not_applicable_value_is_not_the_phrase_not_applicable`) — the governed value is not collateral damage of this gate |

**§8 is structural, not cosmetic.** `result_presence` is always `null`, and the
payload carries `result_presence_note`:

> Capability and results are different facts. This projection states what the
> product supports; it carries no result for any organisation. A requirement with
> no current result is not an unsupported requirement, and an unmeasured
> requirement is never zero emissions.

Both surfaces render that statement under the heading **"Capability is not a
result"**, and every requirement row/panel carries *"No result is stated here for
any organisation."*

---

## 15. `AG-5` — no tenant identifier and no tenant query

**Gate:** *"The investor surface contains **no** tenant identifier and issues
**no** tenant-table query — route/query audit + identifier scan."* (`SEC-1`,
`SEC-3`, `CS-1`, `§19.4` row 8)

**P17-L status: CLOSED**, by both halves of the gate (identifier **and** path).
See §12 for the full table. The load-bearing evidence:

* **Query path:** `test_no_tenant_query_is_issued_by_the_read_model` attaches a
  query logger to a real connection and asserts that **not one** statement names
  a tenant table or reads `current_setting`/`auth.uid`;
  `test_the_route_issues_at_most_three_read_queries` proves the surface adds no
  extra query of its own.
* **Identifier scan:** 8 tenant tokens over the serialised payload (API +
  runtime) and over the rendered DOM (frontend), including a real organisation
  UUID harvested in the same test run.
* **Route audit:** the OpenAPI operation declares **no parameters** at all.
* **Surface audit:** a static assertion that the product page does not reference
  `resolveV3Organization`, `organizationId`/`organization_id`, or any
  facility/supplier/report/snapshot endpoint.

---

## 16. `AG-7` — the four-way rollup, never a total

**Gate:** *"The four-way rollup is shown, not a total — summary assertion."*
(`S3-1`)

**P17-L status: the rendering branch is now CLOSED.** See §10. The gate is
enforced at four levels: the projection derives the split from the rows (and
refuses a value outside the four buckets), the API asserts the exact `4/6/3/2`
and the absence of any coverage/total/percentage/score/materiality/assurance
**field**, the runtime suite re-derives it in SQL, and the rendered surface is
asserted to contain the four buckets with their counts and no `n/15` or `%`
expression.


---

## 17. `AG-8` — every claim has provenance or an explicit unresolved marker

**Gate:** *"Any illustrated result on the investor surface resolves to persisted
data with provenance — provenance-chain check."* (`IN-2`)

`P17-L`'s surfaces illustrate **no result** (deliberately — see §8/§21), so the
gate's *result* branch is satisfied vacuously **and honestly**: the surface makes
no claim that would need a result chain. What the gate can and does check on this
surface is the **claim** branch, and it is closed:

| Check | Verification |
|---|---|
| Every requirement carries a `source_locator`, an `authoritative_text_ref` and a `source_tier` ∈ {1,2,3} | unit + API + runtime, over the **persisted** rows |
| The rendered identifier state **equals** the persisted `identifier_status` | runtime, per requirement |
| An unresolved status is always accompanied by `official_identifier IS NULL` | runtime (`test_ag_8_no_official_identifier_is_invented`: 0 violations) |
| The framework version carries its own source (`version_label`, `status`, `source_tier`, `source_url`) | API + surface; an absent authority date stays `null` rather than being guessed |
| The rendered surface shows the marker | frontend: *"Authoritative identifier unresolved"* and *"Source tier 1"* asserted in the DOM |

**Nothing was invented**: no official identifier, no source date, no URL, no
methodology claim.

---

## 18. Real PostgreSQL

### 18.1 The target

| Item | Value |
|---|---|
| Clone | `ct_p17l_surface_20260926` on `127.0.0.1:54426` |
| How it was built | `CREATE DATABASE ct_p17l_surface_20260926 TEMPLATE ct_p17k_20260926` — i.e. a copy of the P17-K verification clone, which carries the Phase-8 B1 disclosure foundation **and** the five authorised P17 migrations **and** the P17-K catalogue |
| F-046-1 marker check | the name contains none of `qa` / `demo` / `investor` / `prod` / `live` |
| Catalogue at start | `disclosure_requirement_versions` = 18 on the evidenced version, `disclosure_framework_versions` = 1 |
| Tenant disclosure state | `disclosure_applicability_assessments` = 0, `disclosure_values` = 0 (a clean baseline for the isolation checks) |
| Catalogue after the destructive fixture ran | **18 rows on the evidenced version — unchanged** |

`TEMPLATE` is read-only for the source, so the P17-K clone was never written to
*by P17-L*. It was later used as the comparison target for the pre-existing
disclosure failures (§20.2/§20.3), which is where its current residue comes from;
the governed catalogue on the evidenced version (18 rows) is intact in both
clones.

### 18.1.1 A defect this suite found and this task fixed (P17L-F2)

Running the P17-K runtime suite **before** the P17-L suite on the same clone
produced this:

```text
domain.disclosure.DisclosureViolation: P17-L: requirement code 'B1RT_068e737e'
is not a governed disclosure requirement identity (GP-S1 / GP-S2-LB / GP-S2-MB /
GP-S3-CAT-NN); refusing to invent a scope or category for it
```

…and the surface answered **503** — which is the fail-closed behaviour working
correctly, and simultaneously proof of a **real latent defect in the read
model**: the first revision filtered the catalogue by framework **code**, so a
second version of the same framework (`B1RT-*`: test residue, a future
catalogue, another standard's rows) merged into the claim and took the whole
statement down.

**Fix.** The surface now selects the governed catalogue **version** by rule,
never by ordering: `capability_catalogue_candidates()` returns the framework
versions that carry requirement rows together with their codes, and the route
picks the first candidate that carries at least one **governed** requirement
identity — checked with `domain.capability_catalogue.is_governed_requirement_code`,
so the grammar stays defined in exactly one place. Requirements are then read by
`framework_version_id`, never by framework code.

**Regression guards.** `test_the_governed_catalogue_version_is_selected_not_the_first`,
`test_the_requirements_are_scoped_to_the_selected_version`,
`test_a_database_with_only_ungoverned_requirement_rows_yields_no_claim` (unit/API)
and `test_a_second_framework_version_never_widens_the_catalogue` (real
PostgreSQL: it inserts a junk version + row, asserts the surface still returns
exactly the governed 18, and removes the rows in a `finally` block so the clone
is left as found).

**Verified after the fix:** the combined run
(`test_p17k_…_runtime.py test_p17l_…_runtime.py`, 61 tests) is **green on a clone
that already contains the P17-K residue** — which is the strict-ordering test
that found the defect.

### 18.2 The ten required checks

| # | Required | Result |
|---|---|---|
| 1 | catalogue exists | **PASS** — the evidenced version label, `IN_FORCE`, `source_tier` 1, 18 rows |
| 2 | catalogue rows are unchanged | **PASS** — count, `max(updated_at)` and a `hashtext` signature of every `(requirement_code, carbontally_capability)` pair are identical before and after the projection **and** an HTTP read |
| 3 | projection returns expected rows | **PASS** — 18 rows; scopes `{Scope 1, Scope 2, Scope 3}`; Scope 3 categories exactly 1…15; Scope 2 methods exactly `{LOCATION_BASED, MARKET_BASED}`; every row carries name, class, explanation and detail |
| 4 | exact `M-1` mapping preserved | **PASS** — all 15 categories equal the frozen image, in the **projection** *and* in the **persisted** rows; the 6 bounded categories are still `PARTIALLY_SUPPORTED` (`S3-2`) |
| 5 | four-way rollup exact | **PASS** — `4/6/3/2` from the projection, from a direct recomputation, and from a `GROUP BY` in SQL |
| 6 | no applicability model exists | **PASS** — no applicability token is persisted in `requirement_class`/`carbontally_capability`; no applicability column exists; the payload contains neither `applicability`, `does_not_apply` nor `assessed_status` |
| 7 | no tenant data is returned | **PASS** — 8 tenant tokens absent from the payload; no tenant column on the catalogue; no FK path to a tenant table |
| 8 | negative tenant isolation test | **PASS** — JWT-level and HTTP-level: two tenant contexts produce byte-identical capability truth; two real organisations produce byte-identical HTTP responses; an authenticated non-org actor is served the same product truth |
| 9 | demo database refused by the safety probe | **PASS** — a subprocess pointed at `carbontally_demo_local` exits non-zero in **fixture setup** with the explicit `F-046-1` refusal text, and the demo database's catalogue counts are identical before and after |
| 10 | production untouched | **PASS** — production never contacted; `carbontally_demo_local` unchanged (catalogue 0, `organizations` 4 before and after); `carbontally_test` untouched (asserted); the P17-K clone used only as a read-only `TEMPLATE` **by P17-L** (see §18.1 — its later residue comes from the pre-existing-failure reproduction, and its governed 18-row catalogue is intact) |

### 18.3 Run

```bash
INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_p17l_surface_20260926 \
  .venv/bin/python -m pytest tests/integration/test_p17l_capability_truth_surface_runtime.py
```

Result: **37 passed** — including a full HTTP round-trip through the real ASGI
app (`httpx.ASGITransport`) on the real database, a subprocess run that points a
destructive suite at the demo database and proves it is refused before any
`TRUNCATE`, and a version-scoping regression that inserts a conflicting framework
version, proves the claim does not widen, and removes its rows in a `finally`
block. The combined run with the P17-K runtime suite (**61 passed**) is the
strict-ordering test that found `P17L-F2` and now proves it fixed.


---

## 19. Regression

| Suite | Command | Result |
|---|---|---|
| New — projection (unit) | `pytest tests/unit/domain/test_capability_catalogue_projection.py` | **72 passed** |
| New — API (unit) | `pytest tests/unit/api/test_p17l_capability_truth_surface.py` | **58 passed** |
| New — surface (frontend) | `react-scripts test --testPathPattern capability-truth-surface` | **19 passed** |
| New — runtime (integration, real PG) | see §18.3 | **37 passed** |
| Combined strict-ordering run (the defect trigger) | `pytest tests/integration/test_p17k_…_runtime.py tests/integration/test_p17l_…_runtime.py` | **61 passed** |
| P17-K unit | `tests/unit/data/test_p17k_governed_capability_catalogue.py`, `tests/unit/data/test_p17_migrations.py` | **passed** |
| P17-K integration (real PG) | `tests/integration/test_p17k_governed_capability_catalogue_runtime.py` | **24 passed** |
| `tests/unit/domain/` (all) | `pytest tests/unit/domain/` | **passed** |
| `tests/unit/data/` (all) | `pytest tests/unit/data/` | 3 known failures (see §20) |
| Disclosure B1 (real PG) | `tests/integration/test_disclosure_b1_runtime.py` | 1 pre-existing failure (§20) |
| Disclosure B3 projection (real PG) | `tests/integration/test_disclosure_b3_projection_runtime.py` | 1 pre-existing failure (§20) |
| Disclosure B3 V3 security (real PG) | `tests/integration/test_disclosure_b3_v3_security.py` | 9 pre-existing setup ERRORs (§20) |
| Disclosure B4 finalisation (real PG) | `tests/integration/test_disclosure_b4_finalisation_runtime.py` | **19 passed** |
| Frontend — whole suite | `react-scripts test --watchAll=false` | **475 passed, 1 failed, 2 suites failed** (both pre-existing — §20) |
| Wider backend unit suite | `pytest tests/unit` | **exactly the 9 known baseline failures** (§20) |

**P17-05 … P17-10** are covered by the `tests/unit/api/test_p17_*.py`,
`tests/unit/services/test_p17_*.py` and `tests/integration/test_p17_*.py` suites,
all of which were run as part of these sweeps and show no new failure.

Two of my own suites are *self-verifying regression gates* in their own right:
`test_the_route_cannot_be_mounted_twice` and
`test_no_second_capability_named_route_exists` would fail if a future change
added a duplicate capability endpoint (`§16`), and
`test_the_read_path_writes_nothing` would fail if a future change made the read
surface mutate the governed catalogue.

---

## 20. Known baseline failures

### 20.1 The nine wider-unit-suite baseline failures — UNCHANGED

Identical list and count to the P17-K baseline; none is related to P17-L (none
touches the disclosure module, the capability projection or the frontend):

| # | Suite :: test | Nature |
|---|---|---|
| 1–3 | `tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained`, `::test_canonical_ops_review_assign_registered`, `::test_canonical_ops_sla_surface_registered` | pre-existing review/SLA route-registration assertions |
| 4 | `tests/unit/data/test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged` | pre-existing migration-ordering assertion |
| 5 | `tests/unit/data/test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration` | pre-existing "latest migration" assertion (superseded before this task) |
| 6 | `tests/unit/data/test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy` | same class as #5 |
| 7–9 | `tests/unit/engines/test_extraction_suggestions.py::test_suggest_parses_clean_invoice`, `::test_suggest_missing_fields_leave_unresolved`, `::test_suggest_no_fabrication_on_garbage` | pre-existing extraction-suggestion failures |

**The wider suite is therefore NOT green, and is not claimed as green.**
`P17-L` adds **no migration**, so it cannot have changed the migration-ordering
assertions; and it touches neither review/SLA routes nor extraction suggestions.

### 20.2 The two frontend baseline failures — VERIFIED PRE-EXISTING

| Suite | Failure | How "pre-existing" was established |
|---|---|---|
| `src/App.test.js` | jest module-resolution error on `react-router-dom` imported at `src/App.js:4` | **stash-verified**: with every P17-L frontend change stashed (`git stash push -u`), the suite fails identically (2 suites failed, 1 test failed). The unresolved import is on an untouched line. Restoration verified by `md5sum` equality and an empty stash list |
| `src/v3/__tests__/dr007-investor-display-fixes.test.jsx` | `DR-007 … Issue 3 — customer review detail shows Mapped activity from mapped_data.activity` | **stash-verified** in the same run; the test imports `customer/ProcessingItemWorkspace` and `customer/ReviewDetailPage`, neither of which P17-L touches |


### 20.3 A pre-existing environmental gap discovered during regression (P17L-F1)

**Finding.** Three disclosure suites cannot pass on a *chain clone*, because
`disclosure_intensity_denominator_types` holds **0 reference rows** there:

| Database | `disclosure_intensity_denominator_types` |
|---|---|
| `ct_p17l_surface_20260926` (this task) | 0 |
| `ct_p17k_20260926` (P17-K, untouched) | 0 |
| `ct_local_93d5cdd` (baseline clone) | 4 |
| `carbontally_demo_local` | 4 |

The four rows are seeded by
`supabase/migrations/20260917000000_p8_b3_intensity_catalogue.sql` §5 (an
idempotent `INSERT … ON CONFLICT (code) DO NOTHING`), so the chain clones were
evidently not built by applying that migration to that lineage.

**Evidence that this is pre-existing and not caused by P17-L:** the identical
failures reproduce on `ct_p17k_20260926`, an untouched clone that predates this
task — 9 setup ERRORs in `test_disclosure_b3_v3_security.py`
(`TypeError: 'NoneType' object is not subscriptable` on
`disclosure_intensity_denominator_types WHERE code = 'NET_REVENUE'`), one failure
in `test_disclosure_b1_runtime.py::test_rls_actor_boundary_still_enforced`, and
one in `test_disclosure_b3_projection_runtime.py::test_intensity_catalogue_and_ratio_selection`.

**Disposition:** recorded, **not fixed**. Fixing it means changing test-clone
construction/provisioning, which is outside P17-L's authorisation. It is the same
class of finding as `P17K-F1`.

---

## 21. Remaining limitations

| # | Limitation | Effect | Blocker |
|---|---|---|---|
| **L-1** | **The capability catalogue is NOT promoted.** `carbontally_demo_local` still has 0 catalogue rows | The surfaces return **503** ("no capability statement") on any environment without the catalogue. That is the fail-closed behaviour working as designed — **not** a defect — but the surface is not yet *usable* outside a database carrying the P17-K catalogue | the **deployment gate** (`DECISION-03 §18.1` Tier 1 item 5): apply `p17a`/`p17c`/`p17d`/`p17h`/`p17_10` + the P17-K catalogue to the hosting environment. Promotion is a deployment act, not a development one |
| **L-2** | **`P17-J` (Scope 2 end-to-end acceptance) is outstanding** | The Scope 2 panel states *capability* only; no Scope 2 result path is claimed anywhere | separate acceptance gate — explicitly **not** absorbed (`§20`) |
| **L-3** | **`PO-5` (the name of the "no data supplied" state) is still open** | The surfaces deliberately label **no** absence state; a requirement with no result renders the neutral line *"No result is stated here for any organisation."* | PO decision. `IV-4`/`CS-3` require showing less rather than inventing a name |
| **L-4** | **`result_presence` is `null` on this projection** (§8/§14) | Per-organisation result presence is **not** shown on either surface | design decision: §8 forbids conflating capability with results; §13/`SEC-1` forbid reading tenant data from this path; `PO-5` forbids naming the absence state. A per-category tenant result-presence view would be a **separate tenant-scoped read model**, not an extension of product truth |
| **L-5** | **`AG-8`'s illustrated-result branch is vacuous** | No result is illustrated, so no result provenance chain is exercised | by design (`§9.4`, `IN-2`); it becomes live only when a result-carrying capability surface is built |
| **L-6** | **`P17K-F1`** — the P17-09/P17-10 integration suites are not reproducible-green on a clone of the current demo schema (`calculation_snapshots.performed_by` Gate-4 FK vs a random-UUID fixture) | unchanged by P17-L | PO/implementation decision (carried forward from P17-K) |
| **L-7** | **`P17K-F2`** — `DECISION-03 §12.1` cites a non-existent column (`applicability_status`; the real column is `assessed_status`) | the frozen document was **not** edited | PO/implementation decision (carried forward from P17-K) |
| **L-8** | **`P17L-F1`** — chain clones lack the `disclosure_intensity_denominator_types` seed (§20.3) | 11 pre-existing disclosure-suite failures/errors on chain clones | test-clone provisioning — outside this task's authorisation |
| **L-8b** | **`P17L-F2`** — the read model first filtered by framework code, so a second version of the same framework merged into the claim (§18.1.1) | **FOUND AND FIXED BY THIS TASK**, with four regression guards (unit/API + real-PostgreSQL). Not a residual limitation | none — closed |
| **L-9** | The product/investor surface has **no navigation entry** (reached at `/capabilities/product`, cross-linked from `/capabilities`) | deliberate: a second D18 nav entry was not warranted, and a product/due-diligence view is a direct-URL demo surface | no blocker; revisit if a Product/About area is ratified |
| **L-10** | **Not independently verified** | see §25 | OHD/QA pass |


---

## 22. Investor / customer implications

### 22.1 What is now *sourced* rather than *asserted*

Before P17-L, `DECISION-03 §9.3`'s required investor claims had a governed
catalogue home (P17-K) and no reading surface. The nine `§9.3` items are now
either **rendered** or **explicitly not rendered**, and the distinction is
testable:

| `§9.3` item | Where it lives on the product surface |
|---|---|
| 1. What is supported | the Scope 3 table, per category, governed value verbatim |
| 2. What is calculated and persisted | **not claimed** — no result is illustrated (`IN-1`); the surface states capability only |
| 3. What is estimated | **not claimed** (no result is illustrated) |
| 4. What is under review / not reportable | **not claimed** on this surface — that is the existing reportability lifecycle, reached from Reports |
| 5. What has evidence | **not claimed** as a coverage figure (`F-8`); evidence concepts may appear only where actually supported |
| 6. Which methodology and factor were used | **not claimed** (no result is illustrated) |
| 7. What is unsupported | rendered plainly: `MISSING_CAPABILITY` / `FUTURE` rows with their named prerequisite |
| 8. What depends on customer data | expressed through the governed input-limited values where the catalogue records them (`STRUCTURED_INPUT_REQUIRED` / `EXTERNAL_INPUT_REQUIRED`) |
| 9. Disclosure is a separately-governed concern | the surface states that these are product capability facts — not applicability, not a compliance conclusion, and not an emissions result |

### 22.2 The commercial effect (as a fact, not a commitment)

* A capability claim shown to an investor or a customer now comes from a
  **persisted governed row**, read through **one** projection, and rendered
  **identically** on both surfaces. `CM-1`/`CM-2` (no `architecture_status`; the
  same values as the product) can now be checked mechanically rather than by
  review.
* The four-way rollup `4 / 6 / 3 / 2` is the honest expression `S3-1` requires,
  and the surface cannot produce `"all 15"`, a coverage percentage or a total —
  those are test failures, not style violations.
* The Scope 2 market-based claim remains **not** producible, and the surface says
  so plainly (`SC-4`).
* **What is still not sellable from this surface:** anything requiring a
  *result* (`IN-2`), and anything requiring applicability or materiality
  (`PO-3`). `L-1` (promotion) and `L-2` (`P17-J`) remain before either surface is
  usable in a hosted environment.

### 22.3 For the customer

The customer can now answer `§8`'s question 1 (*"what can CarbonTally do for
me?"*) in governed vocabulary, with the prerequisite named and the
CarbonTally-limitation vs customer-input distinction preserved (`CT-3`). They
are **not** shown a compliance conclusion (`CT-2`) and their own numbers are
never inferred from capability (`§8`).

---

## 23. Production safety

| Item | Result |
|---|---|
| Production contacted | **NO** |
| Demo database (`carbontally_demo_local`) | **read-only**; two `SELECT count(*)`s; verified unchanged (catalogue 0 \| 0; `organizations` 4 before and after) |
| `carbontally_test` | **not touched**; the runtime suite asserts its own target is not that database |
| P17-K evidence clone (`ct_p17k_20260926`) | used **read-only** by P17-L (a `TEMPLATE`, read-only for the source). Its later residue is from the pre-existing-failure reproduction in §20.2/§20.3, which targets chain clones; its governed 18-row catalogue is intact. It is a disposable `ct_*` clone |
| Disposable clone (`ct_p17l_surface_20260926`) | created for this task; the only database mutated (and only through the standard destructive integration fixture) |
| Migration applied to any non-disposable environment | **none** — P17-L adds no migration |
| F-046-1 | restated in the integration module docstring **and** enforced by a subprocess test that points a destructive run at the demo database and proves it is refused in fixture setup |
| Secrets | no credential, JWT, signed URL, connection string or demo password appears in this report or in any committed file |
| Push | **NO** |
| `.gitignore` | **not modified** by this task |
| Pre-existing untracked files | **not staged, not committed** |


---

## 24. Commits

### 24.1 Commit list

| # | SHA | Subject | Files |
|---|---|---|---|
| 1 | _recorded in §24.2_ | `feat(p17-l): canonical governed capability projection + capability read endpoint` | `backend/domain/capability_catalogue.py` (new), `backend/data/disclosure.py`, `backend/api/v3_disclosure.py`, `backend/tests/unit/domain/test_capability_catalogue_projection.py` (new), `backend/tests/unit/api/test_p17l_capability_truth_surface.py` (new), `backend/tests/integration/test_p17l_capability_truth_surface_runtime.py` (new) |
| 2 | _recorded in §24.2_ | `feat(p17-l): customer + product capability truth surfaces (one canonical projection)` | `frontend/src/v3/components/CapabilityTruthSurface.jsx` (new), `frontend/src/v3/capabilities/{CapabilitiesPage.jsx,InvestorCapabilityPage.jsx,capabilities.css}` (new), `frontend/src/v3/__tests__/capability-truth-surface.test.jsx` (new), `frontend/src/v3/api.js`, `frontend/src/App.js`, `frontend/src/v3/components/V3Layout.jsx` |
| 3 | _recorded in §24.2_ | `docs(p17-l): implementation report` | `docs/architecture/CT-PO-P17-L-CAPABILITY-TRUTH-SURFACE-20260926.md` (new) |
| 4 | _recorded in §24.2_ | `docs(p17-l): record the implementation-report commit SHAs` | this document (§24.2) |

### 24.2 Recorded SHAs

| Item | SHA |
|---|---|
| Starting SHA (`P17-L` baseline) | `3f3dfa415abc8f8d0767ad4f5339a2cefc9e1e12` |
| Commit 1 | PENDING — recorded by the follow-up `docs(p17-l)` commit |
| Commit 2 | PENDING — recorded by the follow-up `docs(p17-l)` commit |
| Commit 3 | PENDING — recorded by the follow-up `docs(p17-l)` commit |
| Commit 4 | PENDING — recorded by the follow-up `docs(p17-l)` commit |
| Ending SHA | PENDING — see the final response accompanying this task |

### 24.3 Git discipline

* Branch: `p8-release-reconciled`. **Nothing was pushed.**
* No `git reset --hard`, no `git clean -fd`, no force-push, no history rewrite.
* Only P17-L files were staged, by explicit path. The pre-existing `.gitignore`
  modification and every pre-existing untracked file remain untracked and
  unmodified.
* Commit identity: `Cline <cline@carbontally.local>`.
* `P17-L` adds **no** migration, so no database version was advanced.

---

## 25. Final verdict

> **`P17_L_IMPLEMENTATION_COMPLETE`**

with the following **explicit non-claims**, each of which the contract requires
be stated:

1. **No capability catalogue is promoted to any hosted environment.** The
   surfaces return `503` with a friendly message wherever the governed catalogue
   is absent (`carbontally_demo_local` today). That is fail-closed behaviour, not
   a defect — and it means the surfaces are **not yet usable in a hosted
   environment** (`L-1`). Promotion is a **deployment gate**.
2. **`P17-J` / Scope 2 end-to-end acceptance is OUTSTANDING** and was not
   absorbed (`§20`).
3. **`PO-5` is still open**; no absence state is named (`L-3`).
4. **`result_presence` is deliberately `null`** on this projection (`L-4`).
5. **`AG-8`'s illustrated-result branch is vacuous** because no result is
   illustrated (`L-5`).
6. **`P17K-F1`, `P17K-F2` and `P17L-F1` remain open** (`L-6`…`L-8`).
   **`P17L-F2` was found by this task and fixed** (§18.1.1): the read model first
   filtered by framework code, so a second version of the same framework merged
   into the claim. The corrected surface selects the governed version by rule and
   is covered by four regression guards, including a real-PostgreSQL test that
   inserts a conflicting version and proves the claim does not widen.
7. **Not `ACCEPTED`.** No PO or investor acceptance decision was sought or
   obtained.
8. **Not `INDEPENDENTLY VERIFIED`.** Every claim here was produced by the
   implementing agent. An OHD/QA pass is required.
9. **Not `PRODUCTION READY`.** Nothing was deployed.
10. **Production contacted: NO. Pushed: NO.**

### 25.1 The term-by-term position

| Term | Position | Evidence |
|---|---|---|
| **IMPLEMENTED** | YES | 1 new domain module, 1 additive repository method, 1 route, 3 frontend modules + 1 shared component + 1 stylesheet, 4 test modules, 4 modified files |
| **PERSISTED** | YES (pre-existing) | 18 governed `disclosure_requirement_versions` rows + 1 `disclosure_framework_versions` row + 2 CHECK constraints — **P17-K's**, re-verified, unchanged, and untouched by this task's read path |
| **READABLE** | YES | `GET /api/v3/capabilities` returns the canonical projection to an authenticated caller; proven over real PostgreSQL via a real ASGI round-trip |
| **E2E VERIFIED** | YES — for the capability surface | customer (`/capabilities`) and product (`/capabilities/product`) surfaces render the same payload; 19 frontend tests; both surfaces asserted to show the same governed value per requirement |
| **REAL-PG VERIFIED** | YES | 37 integration tests on the disposable clone `ct_p17l_surface_20260926` (§18), plus a 61-test combined run with the P17-K suite |
| **INDEPENDENTLY VERIFIED** | **NO** | implementer-produced only |
| **ACCEPTED** | **NO** | no PO/investor decision |
| **PRODUCTION READY** | **NO** | not deployed; `L-1` promotion outstanding |

### 25.2 What a reader may and may not conclude

* **May conclude:** the governed capability catalogue now has exactly one
  canonical read/projection; a customer surface and a product surface consume the
  same capability truth; `AG-3`, `AG-4`, `AG-5`, `AG-7` and the claim branch of
  `AG-8` are enforced by automated tests at the projection, API, runtime and
  rendered-DOM levels; the four-way rollup is the honest Scope 3 expression and
  no total, coverage figure, applicability claim or internal architecture status
  is reachable.
* **May not conclude:** that any capability claim is *accepted* or
  *independently verified*; that the surfaces are live anywhere; that Scope 2 is
  end-to-end accepted; or that the wider test suite is green — it is not, and the
  known failures are listed in §20 unchanged.

