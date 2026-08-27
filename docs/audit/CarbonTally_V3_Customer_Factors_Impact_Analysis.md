# CarbonTally V3 Customer-Owned Emission Factors
# Impact Analysis

Status: **READ-ONLY IMPACT ASSESSMENT — NO IMPLEMENTATION**
Date: 2026-08-09 · Branch: `main`
Mode: Read-only. No code, database, migration, RLS, Storage, API, frontend or
test changes were made. Factor baseline unchanged (7,049).
Baselines used: `docs/cline/CarbonTally-v2.1-Traceability-Matrix-v1.0.md` and
`docs/cline/CarbonTally-V3-Impact-Assessment-v1.0.md`.

---

## 1. Executive Summary

CarbonTally does **not** currently support customer-owned emission factors, in
either the v2.1 backend or the legacy application. Every factor that reaches
matching or calculation is resolved from a CarbonTally-managed reference
(`emission_factors` in v2.1; `defra_conversion_factors` in legacy). There is no
org-owned factor representation, no customer-factor API, and no customer-factor
RLS.

**What exists and can be reused:**
- v2.1 engines (matching pipeline, calculation × multiplier, snapshot/hash/verify)
  are factor-domain-agnostic and can be **extended** — not redesigned — to accept
  customer factors shaped like `EmissionFactor` with `factor_source='CUSTOMER'`.
- The org-scoped isolation pattern already exists in `factor_aliases`
  (`organization_id IS NULL OR is_org_member(organization_id)` RLS), and the
  `is_org_member()` helper is available.
- `calculation_snapshots` already preserves factor_id, co2e_multiplier,
  factor_source, factor_set and import_batch_id — the lineage backbone exists.
- Legacy manual-entry stores `defra_factor_id` in `emissions_logs`; legacy CSV
  processing ignores customer factor columns and always substitutes the
  CarbonTally DEFRA factor.

**Minimum change (recommended):** a dedicated **`customer_factors`** table
(org-scoped, RLS-isolated, versioned) plus (a) a small matching extension that
presents customer candidates alongside CarbonTally candidates, (b) a calculation
extension that accepts a customer factor and records `factor_source='CUSTOMER'`
in the snapshot, and (c) a customer-factor CRUD/review API. The one unavoidable
schema change is that `calculation_snapshots.factor_id` — currently a NOT NULL
FK to the global `emission_factors` — cannot reference a `customer_factors` row;
it must be relaxed (nullable + owner/kind discriminator) or otherwise made
polymorphic.

**What must NOT be changed:** `emission_factors` (global reference, RLS,
natural key), the 7,049 factors, the matching/calculation math, the existing 19
v2.1 route contracts, and the error envelope.

The 15 critical questions (§25 of the task) are answered explicitly in §33.

---

## 2. Current Emission Factor Architecture

### 2.1 CarbonTally-managed factor domain (the only factor domain today)

| Table | Role | RLS | Natural key | Owner |
|---|---|---|---|---|
| `emission_factors` | v2.1 global factor reference (7,049 rows: DEFRA-DESNZ/GB 7,029 + SEAI/IE 20) | authenticated **SELECT USING(true)** — global read, writes service-role only (RC1/RC2 reference-table policy) | `(reporting_year, activity_type, COALESCE(country,'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))` — no provider_key/org | CarbonTally |
| `import_batches` | versioned import provenance (M1) | deny-by-default | — | CarbonTally |
| `factor_aliases` | global + org-scoped **synonyms** (M6) | `aliases_select_own` (org IS NULL OR is_org_member), `aliases_insert_own`, `aliases_delete_own` | (COALESCE(org,0uuid), alias_text) | CarbonTally global + per-org aliases |
| `defra_conversion_factors` | **legacy** DEFRA store (superseded by `emission_factors`) | legacy | legacy | CarbonTally (legacy) |
| `units` | reference units | authenticated read | — | CarbonTally |

### 2.2 Key facts established by inspection

- `emission_factors` is **global reference data** — authenticated users can read
  every row (`SELECT USING (true)`); there is no organisation dimension. This is
  correct for CarbonTally-managed factors and is the strongest reason **not** to
  bolt customer factors onto this table.
- The factor natural key has no `organization_id` and no `provider_key`; adding
  org-owned rows would require a key rebuild and RLS rework (risky, and rejected
  in §10).
- Provenance fields exist: `factor_source`, `factor_set`, `import_batch_id`,
  `country`, `scope`, `unit`. A customer factor maps cleanly to
  `factor_source='CUSTOMER'`, `factor_set='CUSTOMER'`, `import_batch_id=NULL`.

---

## 3. Current Customer Factor Capability

**Answer: NO customer-owned factor capability exists anywhere.**

| Surface | Current behaviour (traced) |
|---|---|
| v2.1 domain | No `CustomerFactor` type. `domain/factor.py` has only `EmissionFactor`, `FactorSet`, `FactorSetMetadata`. |
| v2.1 repositories | No customer-factor repository. `EmissionFactorsRepository` reads `emission_factors` only. |
| v2.1 API | `POST /api/v2/factor-match` (activity/country/year/unit/scope/org/preferred_provider) and `POST /api/v2/calculate` (`factor_id` → resolved from `emission_factors`) — no customer factor input. |
| Legacy API | `POST /api/emissions` stores optional `defra_factor_id` + client-computed `calculated_kg_co2e`; factor always CarbonTally-managed. |
| Frontend | `ManualEntryStandalone.jsx`/`ManualEntryCore.jsx` load fuel types from `/api/reference/fuel-types` (from `defra_conversion_factors.activity_type`); no customer-factor list exists. |
| DB | No `customer_factors` table; `emissions_logs` stores `emission_factor_id` (RC2 name; legacy `defra_factor_id`) + `metadata` JSONB + `data_source`. |

---

## 4. Current Customer Manual Factor Selection

Traced path: `ManualEntryStandalone.jsx` → `POST /api/emissions` → `emissions_logs`.

1. **Can the customer manually select a factor?** Indirectly (legacy). The
   customer selects `fuel_utility_type` (from `/api/reference/fuel-types`, which
   is derived from `defra_conversion_factors.activity_type`). The factor itself
   is resolved to a CarbonTally DEFRA factor.
2. **Is it a CarbonTally factor?** Yes — always. The reference endpoint reads
   `defra_conversion_factors` (legacy) / `emission_factors` (v2.1).
3. **Is factor_id stored?** Yes — `emissions_logs.defra_factor_id` (legacy
   column; RC2 renamed `emission_factor_id` in the v2.1 repository).
4. **Is the selection validated?** Legacy `POST /api/emissions`: **no**
   (factor_id accepted as-is; `calculated_kg_co2e` is supplied by the client).
   v2.1 `POST /api/v2/calculate`: the `factor_id` is resolved through
   `EmissionFactorsRepository` (existence) and the calculation engine applies
   unit checks (`UnitMismatchError`).
5. **Is the factor frozen into a calculation snapshot?** Legacy: **no snapshots**
   (legacy has no `calculation_snapshots` writes). v2.1: **yes** —
   `CalculationEngine` writes an immutable snapshot (factor_id, co2e_multiplier,
   provenance, content_hash).
6. **Can the customer change the factor?** Legacy: the customer can re-submit a
   record with a different `defra_factor_id`; nothing prevents it. v2.1: the
   customer can call `/calculate` again with a different `factor_id`; a new
   snapshot is appended (old snapshots remain).
7. **Is the change audited?** Legacy: no factor-specific audit. v2.1:
   `audit_trail`/`domain_events` record calculation activity; factor *selection*
   is not itself an audited decision today.
8. **Does changing it trigger recalculation?** Legacy: no automatic recalculation.
   v2.1: recalculation only if a new `/calculate` request is issued.

---

## 5. Current CSV/Excel Factor Handling

Traced paths: `process_emissions.py`, legacy `main copy.py`/`main copy 2.py`,
`frontend/src/App.js` CSV import.

| Question | Answer (traced) |
|---|---|
| Are factor columns in customer CSV/Excel recognized? | **No.** `process_emissions.py` uses a **hard-coded DEFRA dict** (Diesel 2.54, Petrol 2.16); the legacy CSV pipeline maps Standardized Utility/Scope to a DEFRA factor from `defra_conversion_factors` and **overwrites/ignores** any factor column the customer file contains. |
| Are factor values stored? | No customer-supplied value is stored. The CarbonTally DEFRA factor value is applied and the result `calculated_kg_co2e` stored. |
| Are factor IDs stored? | `frontend/src/App.js` CSV import reads `row['DEFRA Factor ID']` — a customer can supply the **id of an existing CarbonTally (DEFRA) factor**, which is stored in `emissions_logs.defra_factor_id`. A custom value cannot be supplied. |
| Are customer factors distinguished from CarbonTally factors? | **No.** There is no distinction — the system always resolves to CarbonTally-managed DEFRA. |
| Are factor values validated? | No (values in the file are ignored; the DB factor is used). |
| Are factor mismatches detected? | **No.** If the customer's file contains a factor different from the CarbonTally factor, the difference is silently overwritten. |
| Does customer review exist? | No factor-level review. |
| Does calculation use the supplied factor? | No — calculation uses the CarbonTally factor that CarbonTally mapped, never a customer-supplied value. |

---

## 6. Current Factor Matching Architecture

- **Engine:** `engines/factor_matching.py` — `FactorMatchingEngine` runs an
  ordered pipeline over a `FactorSearch` index/protocol.
- **Stages** (`engines/matching_stages.py`): Exact → NaturalKey → Alias →
  Keyword → Fuzzy → Semantic (opt-in). Each stage filters the candidate set by
  activity, unit, country, scope, reporting_year and provider context from
  `MatchRequest`.
- **Input contract:** `MatchRequest(id, activity, unit, country, reporting_year,
  scope, organization_id, preferred_provider, max_stages)`.
- **Output:** `MatchResult(status, factor, confidence, methodology, provider,
  stages_executed, suggestions, request_id)` — full explainability.
- **Config:** `MatchingPipelineConfig(stages, fuzzy_threshold,
  keyword_min_confidence, semantic_enabled, prefer_provider, restrict_country,
  max_suggestions)`.
- **Index:** `infra/search_index.py` `FactorSearchIndex` (in-memory, loads from
  `emission_factors` via `load_all_for_index`).
- **Organisation dimension today:** only `organization_id` (for alias scoping +
  audit); the candidate set is global CarbonTally factors.

**Conclusion:** the engine is candidate-set-agnostic. Customer factors can enter
as an additional candidate source without touching the pipeline math.

---

## 7. Current Calculation Architecture

- **Engine:** `engines/calculation.py` — `CalculationEngine.calculate(request)`
  computes `quantity × co2e_multiplier` (direct multiply), applies unit checks
  (`UnitMismatchError`), builds `CalculationSnapshot`, verifies reproducibility,
  persists via `CalculationSink`.
- **Input:** `CalculationRequest(match_request_id, organization_id, factor:
  EmissionFactor, quantity, quantity_unit, date, reporting_year, activity,
  activity_type, scope, methodology, source_file/page, log_id, asset_id,
  facility_id)`. **The factor is a matched `EmissionFactor` domain object** —
  ownership is not a concept.
- **Snapshot:** `calculation_snapshots` (M3) preserves `factor_id`,
  `co2e_multiplier`, `factor_source`, `factor_set`, `import_batch_id`,
  `reporting_year`, `methodology`, `algorithm_version`, `content_hash`,
  `calculated_at`, `calculated_by`, `request_id`. Immutable + verify.
- **Constraint:** `calculation_snapshots.factor_id` is **NOT NULL** with FK →
  `emission_factors(id)`.
- **Output contract:** `CalculationSnapshotOut` (v2.1 API) exposes id,
  factor_id, quantity, quantity_unit, co2e_multiplier, co2e_kg, scope, date,
  reporting_year, methodology, algorithm_version, content_hash, source_file/page
  — **provenance fields (factor_source/factor_set/import_batch_id) are in the DB
  row but not the API output**.

**Conclusion:** calculation is ownership-agnostic; the only obstacle to
customer factors is the snapshot FK (§16).

---

## 8. Target Customer-Factor Architecture

Target concept (per the task §4), mapped onto what can be reused:

```
ACTIVITY DATA
   ↓
FACTOR MATCHING                       ← FactorMatchingEngine (EXTEND: add
   ↓                                    customer-candidate source + review hook)
[CANDIDATE SET]
   ├── CarbonTally factors            ← emission_factors (UNCHANGED)
   └── Customer factors               ← customer_factors (NEW, org-scoped)
   ↓
FACTOR REVIEW                         ← NEW customer-review step (customer
   ├── APPROVE → calculation            approves/rejects/selects candidate)
   └── REJECT → CORRECT               ← correction loop (existing workflow)
   ↓
CALCULATION                           ← CalculationEngine (EXTEND: accept
   ↓                                    customer factor; provenance CUSTOMER)
CO2e
```

- The matching/calculation engines are **reused**; the new surface is
  (a) a customer-factor library, (b) a candidate merge + review step, and
  (c) provenance tagging so "which exact factor was used" is always answerable.
- The five-layer approval work from the V3 IA (V3 IA §18) is relevant:
  customer factor review is one layer (customer decision), distinct from entity
  approval and CarbonTally validation.

---

## 9. Customer Factor Ownership

**Requirement:** a customer factor belongs to one `organizations` row and must
not be visible to other organisations; CarbonTally internal staff may have
broader visibility.

| Element | Current state | Assessment |
|---|---|---|
| `organizations` | Tenant table (id, name, …) — no type discriminator | **Reuse** as the owner anchor |
| `organization_members` | Org membership (role IN-list) — used by `is_org_member(uuid)` RLS helper | **Reuse** for owner checks |
| `factor_aliases` | Org-scoped alias rows with `aliases_select_own` RLS (`org IS NULL OR is_org_member(org)`) | **Proven pattern** — replicate for customer_factors |
| `is_org_member()` | RLS helper function (used by M8 policies) | **Reuse** in the new policy |
| Consultants | `consultant_profiles` + `consultant_clients` (consultant↔org link) | **INVESTIGATE** — if consultants access client factors via `consultant_clients` rather than `organization_members`, the RLS predicate must add a consultant clause |

**Recommended ownership model:** `customer_factors.organization_id` NOT NULL →
`organizations(id)`; RLS policy
`USING (public.is_org_member(organization_id))` for authenticated (plus an
admin/staff override predicate for CarbonTally internal users, matching the
existing staff/admin model). This is a **NEW RELATIONSHIP + RLS CHANGE**.

---

## 10. Customer Factor Data Model

### Option A — extend `emission_factors` (REJECTED)

Why rejected:
- `emission_factors` is **global authenticated-read reference data**
  (`SELECT USING (true)`); adding org-owned rows breaks the global model.
- The natural key `(year, activity_type, country, unit, scope)` has no
  organisation dimension → org factors would collide; the index would need a
  rebuild.
- The existing RLS would need conditional policies on a table that all
  customers read globally — high leak risk.
- CarbonTally import provenance (`import_batches`) is global by design.

### Option B — dedicated `customer_factors` table (RECOMMENDED)

Required fields (from the task §6, trimmed to what is actually needed):

| Field | Needed? | Notes |
|---|---|---|
| `id` UUID PK | Yes | |
| `organization_id` UUID NOT NULL FK | Yes | ownership + RLS |
| `name`/`description` | Yes | "My Electricity Factor" |
| `activity_type` VARCHAR | Yes | matching key (align to CarbonTally activity vocabulary) |
| `co2e_multiplier` NUMERIC | Yes | the factor value (the calculation contract) |
| `unit` TEXT | Yes | required for matching + unit validation |
| `scope` TEXT | Yes | scope consistency |
| `country` VARCHAR | Yes | default GB; matches request country |
| `reporting_year` INTEGER | Yes | default current; version scope |
| `factor_source` TEXT | Yes | provenance — `'CUSTOMER'` (or supplier name) |
| `source_reference` TEXT | Optional | customer-defined reference |
| `category`/`supplier_id` | Optional | `supplier_id` FK → suppliers if supplier-specific |
| `effective_from`/`effective_to` DATE | Yes | validity window |
| `status` VARCHAR | Yes | DRAFT/ACTIVE/INACTIVE/ARCHIVED (see §13) |
| `version` INTEGER | Yes | monotonic per factor family |
| `metadata` JSONB | Optional | extensibility |
| `created_by`/`created_at`/`updated_by`/`updated_at` | Yes | audit basics |
| `methodology` | Optional | free-text; no enum to invent |

**Recommended:** a dedicated table. No change to `emission_factors`, its
natural key, or its RLS.

---

## 11. Customer Factor Provenance

Existing provenance structures that can carry customer ownership:

| Structure | Can it represent `owner=CUSTOMER`? |
|---|---|
| `calculation_snapshots.factor_source` | **Yes** — `'CUSTOMER'` (pattern already used for `DEFRA-DESNZ`/`SEAI`) |
| `calculation_snapshots.factor_set` | **Yes** — `'CUSTOMER'` or `<org>-CUSTOM` |
| `calculation_snapshots.import_batch_id` | Set NULL (no CarbonTally batch) |
| `calculation_snapshots.factor_id` | **No** — FK to `emission_factors` (the one obstacle, §16) |
| `emissions_logs.metadata` JSONB | **Yes** — can store owner/source_reference |
| `emissions_logs.data_source` | **Yes** — acquisition method (CSV_UPLOAD, MANUAL_ENTRY…) |
| `audit_trail` / `domain_events` | **Yes** — factor create/edit/approve events |
| `factor_aliases.organization_id` | synonym provenance only (not factor values) |

**Do not invent new enums.** `factor_source` is free-text today (DEFRA-DESNZ,
SEAI); `'CUSTOMER'`/supplier name is consistent. If a structured owner is
desired later, a `factor_owner` column on `customer_factors` (`CUSTOMER` vs
`CARBONTALLY`) is optional — the table itself already implies ownership.

---

## 12. Customer Factor Versioning

**Requirement (task §8):** a historical calculation must not silently change
when a customer edits their factor later.

Current integrity mechanisms:

| Mechanism | Behaviour | Customer-factor adequacy |
|---|---|---|
| `calculation_snapshots` (M3) | Append-only; stores factor_id + co2e_multiplier + content_hash + verify | **Adequate if** the snapshot can reference a customer factor (FK issue §16). The multiplier is frozen, so editing a customer factor never changes an old snapshot. |
| `content_hash` + `verify_reproducibility` | Detects tampering | **Reuse** — same guarantee for customer factors |
| `report_versions` (legacy) | versioned reports | **Reuse** for report-level history |
| `audit_trail` + `domain_events` | append-only event log | **Reuse** — record factor create/edit/version bumps |
| `customer_factors.version` (new) | monotonic version per factor family; edits create a new version (or bump version, never overwrite) | **NEW** — recommended: new row/version on edit; old versions immutable |
| `emissions_logs` | stores `emission_factor_id` + `calculated_kg_co2e` (operational) | snapshots remain the forensic record |

**Conclusion:** versioning is achievable with **no change to snapshots'
immutability** — the version discipline lives in the new `customer_factors`
table (immutable versions, active-row pointer) and the snapshot's frozen
multiplier already guarantees "historical calculations don't change".

---

## 13. Customer Factor Approval

| Concern | Current state | Assessment |
|---|---|---|
| DRAFT/ACTIVE/INACTIVE/ARCHIVED status model | No factor-status model exists. Legacy status patterns: `import_batches.status` (pending/importing/completed/failed/rolled_back), `manual_review_queue.status`, `customer_verifications.status` | **NEW status model** on `customer_factors.status` (DRAFT → ACTIVE → INACTIVE → ARCHIVED). No existing factor-status enum to reuse. |
| Who creates/edits | No concept today | org member with org-admin/editor permission (mirror `require_org_member`/`require_org_admin` in `auth.py`) |
| Who approves | No concept today | **Decision required**: (a) org admin approves own factors, or (b) CarbonTally staff approves. `customer_verifications`/`approval_requests` exist but are tied to **processing assignments** and **documents**, not factors. Reuse the *pattern*, not the tables, or reuse `approval_requests` with `approval_type='FACTOR'` + `metadata` (INVESTIGATE). |
| Who deactivates | No concept today | org admin (or staff) |
| Who uses | org members of the owning org | RLS + matching-scope |

**Recommendation:** status lifecycle on the new table; creation by org editors;
activation/approval per a human decision (org-admin vs staff); no new generic
approval engine — reuse the `approval_requests`/`approval_decisions` pattern
with a `FACTOR` approval_type if a formal approval is required.

---

## 14. Customer Factor vs CarbonTally Factor

The system must preserve the distinction between CARBONTALLY FACTOR and
CUSTOMER FACTOR, and the selected factor must retain its provenance so the
calculation snapshot answers "which exact factor was used?".

| Distinction | Today | V3 (minimum) |
|---|---|---|
| Storage | Only `emission_factors` (+ legacy `defra_conversion_factors`) | `emission_factors` (CarbonTally) + `customer_factors` (customer) — **physically separate tables** |
| Source of truth for value | CarbonTally imports (import_batches) | customer entries with `factor_source`/`source_reference` |
| Selection output | `MatchResult.factor` (EmissionFactor) | `MatchResult` candidates may come from either domain; `EmissionFactor.factor_source` (`'DEFRA-DESNZ'`/`'SEAI'` vs `'CUSTOMER'`) is the discriminator |
| Snapshot provenance | `factor_source`/`factor_set`/`import_batch_id` | `factor_source='CUSTOMER'`, `factor_set='CUSTOMER'`, `import_batch_id=NULL` + `customer_factors.id` |

**Conclusion:** the distinction is preserved by separate tables + the existing
`factor_source`/`factor_set` provenance columns. No new enum needed.

---

## 15. Factor Matching Impact

**Can customer factors enter the existing Factor Matching Engine without a
second engine?** Yes — by **extension**:

1. **Candidate source injection:** extend the search entry point so the
   candidate set = CarbonTally factors (unchanged) **plus** the org's ACTIVE
   customer factors (a `CustomerFactorsRepository.find_active(org_id, activity,
   unit, country, reporting_year)` read, or a `CustomerFactorIndex` mirroring
   `FactorSearchIndex`).
2. **Stage reuse:** exact/keyword/fuzzy/semantic stages operate on candidate
   attributes (activity_type, unit, scope, country, year) — a customer factor
   row exposes the same attributes, so **no stage math changes**.
3. **Precedence:** a **new orchestration step** (not an engine redesign) decides
   candidate ordering — e.g. customer factors first (exact), then CarbonTally,
   mirroring the task's target flow (CUSTOMER FACTORS | CARBONTALLY FACTORS).
4. **Review hook:** `MatchResult.suggestions` already carries alternatives — the
   customer-review screen (approve/reject/correct) is a **frontend + API**
   surface over `factor-match` + `calculate`, not a new engine.
5. **Provenance in output:** `MatchResult.factor.factor_source` already flows
   through `FactorOut`/`FactorMatchOut` — customer origin is visible for free.

**Minimum extension:** one candidate-merge entry + an optional customer-stage
config flag in `MatchingPipelineConfig`. No matching redesign.

---

## 16. Calculation Impact

**Can customer-owned factors be used without a second calculation engine?** Yes —
the math (`quantity × co2e_multiplier`), unit checks, snapshot build, hash and
verify are ownership-agnostic. The factor enters as an `EmissionFactor`-shaped
object with `factor_source='CUSTOMER'`.

**The one real obstacle — snapshot FK:**
`calculation_snapshots.factor_id` is **NOT NULL FK → `emission_factors(id)`**.
A `customer_factors.id` cannot be stored there. Options (decision required):

| Option | Description | Risk |
|---|---|---|
| **O1 — Relax FK + discriminator (recommended)** | Make `calculation_snapshots.factor_id` nullable and add `factor_kind` (`'CARBONTALLY'`\|`'CUSTOMER'`) + optional `customer_factor_id`; enforce exactly-one-factor-source via check constraint | Medium (migration on append-only table; existing rows unaffected if null stays null and checks are `CASE`-based) |
| O2 — Add `customer_factor_id` column, keep `factor_id` NULL for customer factors | Cleaner read model; snapshot still records multiplier + provenance | Low, but introduces two reference columns |
| O3 — Insert customer factors into `emission_factors` with org marker | Avoids FK change | **REJECTED** — breaks global reference model/RLS/natural key (§10) |
| O4 — Separate `customer_calculation_snapshots` table | Clean isolation | **REJECTED** — duplicates the snapshot/verify machinery; violates "no second engine/table duplication" |

`CalculationSnapshotOut` would be extended to expose `factor_source`/`factor_set`
(already in the DB row) so the API can answer "which exact factor was used".

---

## 17. Data Lineage Impact

Current lineage chain (already present):

```
Input data → extraction/normalization → activity → selected factor (id, value)
→ factor ownership (factor_source) → factor version (import_batch_id/set)
→ calculation (methodology, algorithm_version) → CO2e
```

| Requirement ("why did CarbonTally calculate this?") | Supported today | Customer-factor delta |
|---|---|---|
| Activity matched | `MatchResult` + `match_request_id` | unchanged |
| Selected factor identity | `calculation_snapshots.factor_id` | **O1/O2** adds customer factor id |
| Factor value used | `co2e_multiplier` frozen | unchanged |
| Factor ownership | `factor_source` (`DEFRA-DESNZ`/`SEAI`) | `'CUSTOMER'` |
| Factor source/version | `import_batch_id`, `factor_set` | `import_batch_id=NULL`, `factor_set='CUSTOMER'`, version on customer_factors row |
| Calculation method | `methodology`, `algorithm_version` | unchanged |
| Reproducibility | `content_hash` + verify | unchanged |
| Operational record | `emissions_logs.snapshot_id`, `data_source`, `metadata` | unchanged |

**Conclusion:** lineage needs **no new structures**; it needs (a) the snapshot
FK resolution (§16) and (b) optional exposure of provenance in API output.

---

## 18. API Impact

Current API surfaces relevant to customer factors:
- v2.1: `POST /api/v2/factor-match`, `POST /api/v2/calculate` (business);
  `admin/factors` CRUD, `admin/factor-aliases`, `admin/imports`, `admin/audit`
  (admin). Auth via JWT + RBAC (`auth.py`), org isolation via `require_org_member`.
- Legacy: `POST /api/emissions` (accepts `defra_factor_id` + client-computed
  `calculated_kg_co2e`), `GET /api/reference/fuel-types`, `POST /api/upload`
  CSV processing.

Required V3 customer-factor API (per task §17) and whether the existing patterns
extend:

| Endpoint (target) | Current pattern to extend | Notes |
|---|---|---|
| `POST /api/v2/customer-factors` | admin `POST /factors` pattern | org editor creates DRAFT |
| `GET /api/v2/customer-factors?org_id=` | `GET /factors` pattern | org-scoped list (RLS + repo filter) |
| `GET /api/v2/customer-factors/{id}` | `GET /factors/{factor_id}` pattern | |
| `PUT /api/v2/customer-factors/{id}` | `PUT /factors/{factor_id}` pattern | version bump + audit |
| `DELETE`/deactivate `/customer-factors/{id}` | `DELETE /factors/{factor_id}` pattern | prefer soft-deactivate (status → ARCHIVED/INACTIVE) to protect snapshots |
| `POST /api/v2/customer-factors/{id}/approve` | approval pattern (admin/review) | per §13 decision |
| `POST /api/v2/factor-match` (extend) | existing — add customer candidates | `organization_id` already in `FactorMatchIn`; response adds customer-origin factors |
| `POST /api/v2/calculate` (extend) | existing — accept `customer_factor_id` OR resolve customer factor | `factor_id` today resolves via `EmissionFactorsRepository`; add a customer-factor resolver branch |

**Conclusion:** the v2.1 route/repository/contract patterns extend cleanly
(additive routes, no existing contract broken). The 19-route surface grows by
~7 customer-factor routes.

---

## 19. RLS Impact

Audit targets: Customer A must not see Customer B's factors; consultants and
CarbonTally staff per existing permissions.

| Table | Current RLS | V3 change |
|---|---|---|
| `emission_factors` | authenticated SELECT USING(true); writes service-role | **NO CHANGE** — global reference stays global |
| `customer_factors` (NEW) | — (deny-by-default) | **RLS CHANGE** — `customer_factors_select_own` USING `is_org_member(organization_id)`; INSERT/UPDATE for members (role-checked); DELETE restricted (or none — soft-deactivate) |
| `calculation_snapshots` | `calc_snapshots_select_own` USING `is_org_member(organization_id)` | **NO CHANGE** — already org-scoped |
| `factor_aliases` | aliases select/insert/delete-own | **NO CHANGE** |
| `import_batches`, `domain_events` | deny-by-default | **NO CHANGE** |
| `emissions_logs` | org-scoped (RC2) | **NO CHANGE** |

Consultant access: if `consultant_clients` is the consultant→org link and
consultants are **not** `organization_members` of client orgs, `is_org_member`
won't grant factor access — the policy must add
`OR is_consultant_of(organization_id)` (mirrors the RC2 org-isolation decision
for emissions). **INVESTIGATE the exact consultant membership model before
writing the policy** (flagged in §31).

CarbonTally internal access: staff/admin role override predicate — consistent
with the existing staff admin model.

**Required RLS changes:** ONE new table's policies (select/insert/update/delete
for `customer_factors`), reusing `is_org_member()`. No changes to existing
tables.

---

## 20. Storage Impact

Customer factor evidence (task §19: methodology, source documents, supplier
documents, certificates, calculation basis) may need Storage.

Current Storage architecture (legacy Supabase):
- Private buckets only (`documents`, `generated-reports`, `temp-uploads` +
  quarantine); nothing public.
- Tenant-prefixed paths: `documents/<organization_id>/<document_id>/<filename>`.
- Short-lived signed URLs issued after an RLS-checked row read.

Impact:
- No new bucket is required — evidence can live under the existing `documents`
  bucket at `documents/<org_id>/factor-evidence/<factor_id>/<filename>`.
- If evidence rows are attached to `customer_factors`, an RLS check against the
  owning `customer_factors` row gates URL issuance (the legacy pattern already
  re-asserts the owner on every signed-URL request).
- **STORAGE CHANGE: NONE required** if the legacy bucket/path/signed-URL
  convention is reused (optionally a `factor_evidence` join table). If a
  separate `customer-factor-evidence` bucket is preferred, that is an
  **optional** STORAGE CHANGE (new bucket + policies) — decision required.

---

## 21. RBAC Impact

Current roles: v2.1 `auth.py` — `require_auth`, `require_org_member`,
`require_org_admin`; legacy roles (customer/admin/staff/consultant) via
`organization_members.role`.

| Action (task §9) | Role mapping (proposal) | Reuse |
|---|---|---|
| Create customer factor | org member with editor/manager role | extend `require_org_member` chain |
| Edit customer factor | org admin/editor; owner-only | `require_org_member` + owner check |
| Approve/activate | org admin (or staff per §13 decision) | `require_org_admin` |
| Deactivate/archive | org admin or staff | `require_org_admin` |
| Use customer factor in matching/calculation | any org member of owning org | `require_org_member` |
| CarbonTally internal visibility | staff/admin | existing staff model |

**RBAC Impact:** no new role *system*; new **permission boundaries** enforced
by (a) route dependencies (existing `require_org_*` helpers) and (b) RLS.
Consultant clause (see §19) is the only open point.

---

## 22. Database Impact Matrix

Classification keys: NO CHANGE · EXTEND · NEW TABLE · NEW RELATIONSHIP ·
RLS CHANGE · STORAGE CHANGE · UNKNOWN

| Requirement | Existing Structure | Current Support | Change | Risk |
|---|---|---|---|---|
| Customer-factor library storage | `emission_factors` (global) | none | **NEW TABLE** `customer_factors` (org-scoped, versioned) | Medium |
| Customer factor ownership | `organizations` + `organization_members` + `is_org_member()` | strong tenant base | **NEW RELATIONSHIP** `customer_factors.organization_id` FK | Low |
| Customer factor isolation | `factor_aliases` org-scoped RLS pattern | pattern exists | **RLS CHANGE** new policies on `customer_factors` | Medium |
| Factor value persisted | `emission_factors.co2e_multiplier` | CarbonTally only | **NEW TABLE** stores customer values | Low |
| Factor provenance | `factor_source`/`factor_set`/`import_batch_id` on snapshots | global only | **EXTEND** snapshot reference to customer factors (§16 O1/O2) | Medium |
| Historical immutability | `calculation_snapshots` append-only + content_hash | yes | **NO CHANGE** (snapshots unchanged; versioning in new table) | Low |
| Customer factor version history | none | none | **NEW TABLE** version column + immutable version rows | Medium |
| Status lifecycle | none for factors | none | **NEW TABLE** `status` DRAFT/ACTIVE/INACTIVE/ARCHIVED | Low |
| Approval record | `approval_requests`/`approval_decisions` (assignments/docs) | not factor-specific | **EXTEND** (optional) reuse with `approval_type='FACTOR'` | Low |
| Supplier-specific factors | `suppliers` + `supplier_categories` | exists | **NEW RELATIONSHIP** optional `customer_factors.supplier_id` FK | Low |
| Evidence attachments | `documents` bucket + `customer_documents` | legacy | **NO CHANGE** (reuse tenant-prefixed paths) or **STORAGE CHANGE** (optional new bucket) | Low |
| Factor search candidates | `FactorSearchIndex` from `emission_factors` | global only | **EXTEND** candidate set at runtime (no schema change) | Low |
| Global factor reference | `emission_factors` + natural key + RLS | intact | **NO CHANGE** | — |
| Realtime publication | legacy config | none for factors | **UNKNOWN** / out of scope for v3 initial cut | Low |

---

## 23. Backend Impact Matrix

Actions: KEEP · EXTEND · NEW · NO CHANGE · INVESTIGATE

| Requirement | Existing Module | Current Support | Action | Risk |
|---|---|---|---|---|
| Customer factor CRUD | `data/factors_repository.py` | emission_factors only | **NEW** `CustomerFactorsRepository` (org-scoped, versioned, status-aware) | Medium |
| Customer factor domain type | `domain/factor.py` | EmissionFactor/FactorSet | **EXTEND** — add `CustomerFactor` (+ optional `FactorOwner`) | Low |
| Matching with customer candidates | `engines/factor_matching.py` + `matching_stages.py` | pipeline over global set | **EXTEND** — candidate-source injection + customer precedence; no stage redesign | Medium |
| Matching config | `MatchingPipelineConfig` | global filters | **EXTEND** — customer-factor flag/precedence | Low |
| Search index | `infra/search_index.py` | emission_factors only | **EXTEND** — `CustomerFactorIndex` or runtime merge | Low |
| Calculation | `engines/calculation.py` | ownership-agnostic | **EXTEND** — accept customer factor (EmissionFactor-shaped, source=CUSTOMER) | Medium |
| Snapshot persistence | `CalculationSink`/`calculation_snapshots` repo | factor_id FK to emission_factors | **EXTEND** — §16 O1/O2 snapshot reference | Medium |
| Factor review/approval workflow | legacy `manual_review_queue`/`customer_verifications`/`approval_requests` | not factor-specific | **INVESTIGATE** — reuse pattern or `approval_type='FACTOR'` | Medium |
| Factor validation rules | `engines/validation.py` + matching unit checks | global factors | **EXTEND** — customer-factor value rules (range, unit, scope, date window) | Low |
| RBAC enforcement | `auth.py` (`require_org_member`/`require_org_admin`) | strong | **EXTEND** — customer-factor owner/role checks | Low |
| Import (CSV/Excel) | legacy upload pipeline + `ImportMappingEngine` (not built, D2) | CarbonTally factor import only | **NEW** (optional) customer-factor bulk upload path — reuses upload pattern | Medium |
| Evidence handling | legacy document pipeline | documents only | **KEEP** — reuse signed-URL + tenant-prefix convention | Low |

---

## 24. API Impact Matrix

| Requirement | Existing Route/Contract | Current Support | Action | Risk |
|---|---|---|---|---|
| Create customer factor | admin `POST /factors` pattern | emission_factors only | **NEW** `POST /api/v2/customer-factors` | Low |
| List customer factors | `GET /factors` pattern | admin-only | **NEW** `GET /api/v2/customer-factors` (org-scoped) | Low |
| Get customer factor | `GET /factors/{factor_id}` pattern | admin-only | **NEW** `GET /api/v2/customer-factors/{id}` | Low |
| Update customer factor | `PUT /factors/{factor_id}` pattern | admin-only | **NEW** `PUT /api/v2/customer-factors/{id}` | Medium |
| Deactivate customer factor | `DELETE /factors/{factor_id}` pattern | admin-only | **NEW** `DELETE/POST deactivate /api/v2/customer-factors/{id}` (soft) | Medium |
| Approve customer factor | review/approval patterns | documents/assignments | **NEW** `POST /api/v2/customer-factors/{id}/approve` | Medium |
| Factor matching incl. customer factors | `POST /api/v2/factor-match` + `FactorMatchIn` | global only | **EXTEND** — merge customer candidates; `organization_id` already present | Medium |
| Calculation with customer factor | `POST /api/v2/calculate` + `CalculationIn` | `factor_id` → emission_factors | **EXTEND** — resolve `customer_factor_id`; branch in resolver | Medium |
| Snapshot output provenance | `CalculationSnapshotOut` | omits factor_source/set | **EXTEND** — expose provenance fields | Low |
| Error envelope | `core/exceptions.py` + envelope | generic | **NO CHANGE** | — |
| Legacy endpoints | `POST /api/emissions`, `/api/upload` | legacy | **NO CHANGE** (legacy stays; v3 adds v2 paths) | — |

---

## 25. Security Impact

| Concern | Current posture | Customer-factor delta |
|---|---|---|
| Cross-tenant factor leakage | RLS on org tables; global reference is intentionally global | **New RLS on `customer_factors`** (is_org_member) — Customer A cannot read B |
| Injection via factor values | v2.1 repositories use parameterised queries | **KEEP** — same repository discipline for customer factor SQL |
| Forged factor_id in `/calculate` | factor resolved through repository | **EXTEND** — customer-factor resolver must enforce org membership on the factor row |
| Tampered historical calculations | `content_hash` + verify on snapshots | **KEEP** — snapshots immutable; customer edits never rewrite old rows |
| Evidence exfiltration | private buckets + tenant-prefixed paths + short-lived signed URLs | **KEEP** — owner check against `customer_factors` before URL issuance |
| Privilege escalation | `require_org_member`/`require_org_admin` + RBAC | **EXTEND** — factor-level owner/role checks on update/approve/deactivate |
| Factor value sanity | unit checks in calculation; matching validation | **EXTEND** — customer-factor input validation (value range, unit consistency, effective window) |
| Denial via DRAFT flood | legacy rate limits (if any) | **NEW** (optional) quota per org — out of scope for minimum |

**Security verdict:** the v2.1 security posture (RLS + RBAC + parameterised SQL +
hash-verified snapshots + private signed URLs) carries over; the only new
security surface is the `customer_factors` RLS/policy set and the
customer-factor resolver in `/calculate`.

---

## 26. Existing Components to REUSE

1. **`organizations` / `organization_members` / `is_org_member()`** — tenant
   ownership anchor and RLS helper (no new identity machinery).
2. **`factor_aliases` org-scoped RLS pattern** — the exact isolation template
   (`organization_id IS NULL OR is_org_member(organization_id)`) for the new
   `customer_factors` policies.
3. **`FactorMatchingEngine` + matching stages** — candidate-set-agnostic
   pipeline; customer factors enter as candidates (no stage rewrite).
4. **`CalculationEngine`** — `quantity × co2e_multiplier`, unit checks, snapshot
   build, verify — unchanged for customer factors.
5. **`calculation_snapshots` immutability + content_hash + verify** — the
   forensic backbone for "historical calculations must not change".
6. **`factor_source` / `factor_set` / `import_batch_id` provenance columns** —
   carry `CUSTOMER` provenance with no new enum.
7. **`audit_trail` / `domain_events`** — record factor create/edit/approve.
8. **`emissions_logs`** — operational records keep `snapshot_id` link +
   `metadata`/`data_source` for customer-origin context.
9. **`approval_requests` / `approval_decisions`** — pattern (optionally
   `approval_type='FACTOR'`) for formal approval, avoiding a duplicate approval
   system.
10. **Storage convention** — private buckets, tenant-prefixed paths,
    short-lived signed URLs for factor evidence.
11. **v2.1 API route/repository/contract patterns** (admin `factors` CRUD
    template) + `auth.py` `require_org_member`/`require_org_admin` for RBAC.
12. **Error envelope** (`core/exceptions.py`) and v2.1 error codes.

---

## 27. Existing Components to EXTEND

1. **`domain/factor.py`** — add `CustomerFactor` domain type (and optional
   `FactorOwner`), shaped so engines can consume it as an `EmissionFactor`
   (same attributes + `factor_source='CUSTOMER'`).
2. **Factor search entry point** (`infra/search_index.py` + `MatchRequest`) —
   candidate-set injection: global factors + org's ACTIVE customer factors.
3. **`MatchingPipelineConfig`** — customer-factor flag/precedence (customer
   candidates first, CarbonTally fallback).
4. **`engines/calculation.py` / `CalculationRequest`** — accept a customer
   factor and stamp `factor_source='CUSTOMER'` on the snapshot.
5. **`calculation_snapshots` reference** (§16 O1/O2) — allow a customer factor
   id (`customer_factor_id` column + `factor_kind` or nullable `factor_id`).
6. **`POST /api/v2/factor-match`** — return customer-origin candidates alongside
   CarbonTally ones.
7. **`POST /api/v2/calculate`** — resolve `customer_factor_id` (org-checked)
   in addition to `factor_id`.
8. **`CalculationSnapshotOut`** — expose `factor_source`/`factor_set` so the API
   answers "which exact factor was used".
9. **`auth.py` role helpers** — factor-level owner/role checks (editor vs admin).
10. **`engines/validation.py`** — customer-factor input rules (value range,
    unit consistency, effective window, required provenance).

---

## 28. New Components Actually Required

**Minimum set — no more than this:**

| # | Component | Type | Why |
|---|---|---|---|
| 1 | `customer_factors` table | DB (NEW TABLE + RLS + FK) | org-owned factor library; isolation |
| 2 | `CustomerFactorsRepository` | Backend (NEW) | org-scoped CRUD, version bumping, status transitions |
| 3 | `CustomerFactor` domain type | Backend (NEW, small) | typed engine input with provenance |
| 4 | Customer candidate source/merge | Backend (NEW, small) | feed ACTIVE customer factors into matching |
| 5 | Customer-factor resolver in `/calculate` | API (NEW branch) | org-checked customer factor lookup |
| 6 | Customer-factor CRUD + review routes (~7) | API (NEW) | POST/GET/PUT/deactivate/approve + extend factor-match/calculate |
| 7 | `customer_factors` RLS policies | DB (NEW) | org isolation (select/insert/update/delete) |
| 8 | Snapshot FK resolution (§16 O1/O2) | DB migration (NEW) | let snapshots reference customer factors |
| 9 | (Optional) factor evidence link | DB (NEW, optional) | evidence attachments if required |

**Explicitly NOT required:** a second matching engine, a second calculation
engine, a second snapshot system, a new RLS helper function (reuse
`is_org_member`), a new approval engine (reuse pattern), a new enum system, a
customer-factor index table (runtime merge is sufficient at minimum).

---

## 29. Components That MUST NOT Be Created

1. **`customer_factors` in `emission_factors`** (rows in the global reference) —
   breaks global RLS, natural key, import provenance.
2. **A second Factor Matching Engine** — the pipeline is candidate-agnostic;
   duplicate engines create divergence.
3. **A second Calculation Engine** — `quantity × multiplier` + snapshot +
   verify is reused unchanged.
4. **A second snapshot/hash system** — `calculation_snapshots` + `content_hash`
   is the single forensic record.
5. **A duplicate approval system** — reuse `approval_requests`/
   `approval_decisions` pattern (`approval_type='FACTOR'`) instead.
6. **New factor enums** — `factor_source` free-text + `customer_factors` table
   already express ownership.
7. **Legacy-renaming or legacy rewrites** — `defra_conversion_factors`,
   `POST /api/emissions`, `ManualEntryStandalone` stay untouched (D13 deviance
   already records this).
8. **A customer-factor import pipeline in the minimum set** — CSV/Excel bulk
   import is a later increment (§18), reusing the upload pattern.
9. **A separate `customer_calculation_snapshots` table** (O4) — duplicates the
   immutable-snapshot machinery.
10. **Realtime publication for customer factors** — out of scope; no Realtime
    surface in v2.1.

---

## 30. Minimum V3 Change Set

**Database (2 migrations):**
1. `customer_factors` table (org_id FK, activity_type, co2e_multiplier, unit,
   scope, country, reporting_year, factor_source, source_reference, status,
   version, effective_from/to, metadata, created_by/at, updated_at) +
   immutable version discipline.
2. Snapshot FK resolution (§16 **O1** recommended: `factor_id` nullable +
   `factor_kind` + optional `customer_factor_id` with exactly-one-source check).
   No change to `emission_factors`, its natural key, or its RLS.

**RLS (1 migration):**
3. `customer_factors` policies reusing `is_org_member()` (select own-org;
   insert/update member; delete restricted/soft). Consultant clause per
   §19/§31 investigation.

**Backend (NEW + EXTEND):**
4. `CustomerFactor` domain type; `CustomerFactorsRepository` (org-scoped CRUD,
   versioning, status).
5. EXTEND matching entry: merge ACTIVE customer factors as candidates (customer
   precedence, CarbonTally fallback); `MatchingPipelineConfig` flag.
6. EXTEND calculation: accept customer factor; snapshot provenance
   `factor_source='CUSTOMER'`.
7. EXTEND validation: customer-factor value/unit/scope/window rules.

**API (NEW + EXTEND):**
8. ~7 customer-factor routes (create/list/get/update/deactivate/approve) —
   additive; existing 19 contracts untouched.
9. EXTEND `POST /api/v2/factor-match` (customer candidates) and
   `POST /api/v2/calculate` (`customer_factor_id` org-checked resolver);
   expose `factor_source`/`factor_set` in `CalculationSnapshotOut`.

**Explicitly deferred:** customer-factor CSV/Excel bulk import, evidence
bucket, Realtime, quotas, formal two-party approval workflow (pattern-reuse
only if the org-admin-vs-staff decision lands that way).

---

## 31. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Snapshot FK migration on append-only `calculation_snapshots` | Low–Med | High | O1 with CASE-based checks; existing rows untouched; add verify step + regression tests before/after |
| R2 | Customer A sees Customer B's factors via a buggy resolver or RLS gap | Low | **Critical** | RLS as single source of truth; resolver re-checks org membership; integration tests for cross-tenant cases |
| R3 | Consultant access model mismatch (`consultant_clients` vs `organization_members`) | Medium | Medium | **INVESTIGATE** the exact consultant membership before writing RLS; add consultant clause if needed |
| R4 | Matching precedence ambiguity (customer vs CarbonTally both exact-match) | Medium | Medium | Define precedence decision (D-cf) + review step; `MatchResult.suggestions` preserves alternatives |
| R5 | Customer factor edits silently change past figures | Low | High | Immutable version rows + frozen snapshot multiplier + audit; verify hash unaffected |
| R6 | Two reference columns (O2) create read-model confusion | Low | Low | Prefer O1 discriminator; document invariants |
| R7 | Validation gaps (negative/absurd multiplier, unit mismatch) | Medium | Medium | Extend validation rules; unit check already in calculation |
| R8 | Bulk-import demand underestimated | Medium | Medium | Defer; reuse legacy upload pattern; CSV template |
| R9 | Scope creep (approval workflow, evidence, Realtime) | High | Medium | Keep minimum set per §28; decisions per §32 |
| R10 | `emission_factors` accidental change during V3 | Low | **High** | Strict no-change rule (§29); DB untouched in this audit |

---

## 32. Decisions Required

| ID | Decision | Options | Recommended |
|---|---|---|---|
| D-cf-1 | Table choice | (A) extend `emission_factors` / (B) dedicated `customer_factors` | **B** (dedicated table) |
| D-cf-2 | Snapshot reference | O1 relax FK + `factor_kind` / O2 `customer_factor_id` column / O3 emission_factors rows / O4 separate snapshots | **O1** |
| D-cf-3 | Approval authority | (a) org admin approves own factors / (b) CarbonTally staff approves | **a** (org admin), staff override |
| D-cf-4 | Approval mechanism | reuse `approval_requests` (`approval_type='FACTOR'`) / new minimal status-only lifecycle | status-only for minimum; pattern reuse if formal approval required |
| D-cf-5 | Matching precedence | customer-first / CarbonTally-first / customer-exact-only | **customer exact first, then CarbonTally** (per target concept) |
| D-cf-6 | Consultant access | `is_org_member` only / add consultant clause | **Investigate** then decide; align with RC2 emissions access |
| D-cf-7 | Version model | new row per version / single row + version bump | new row per version (immutable), active pointer |
| D-cf-8 | Evidence storage | reuse `documents` tenant-prefixed paths / new bucket | reuse `documents` paths for minimum |
| D-cf-9 | Bulk import | include in V3 / defer | **defer** to later increment |
| D-cf-10 | API exposure of provenance | extend `CalculationSnapshotOut` / internal-only | extend (answers "which exact factor was used") |

---

## 33. Final Recommendation

**Recommendation:** proceed with the minimum V3 customer-factor change set (§30)
using a **dedicated org-scoped `customer_factors` table**, reuse of the v2.1
matching/calculation engines, snapshot provenance via `factor_source='CUSTOMER'`,
and the snapshot FK resolution option **O1**. Scope is limited to the
library/selection/review/calculation path; bulk import, evidence storage and
formal two-party approval are deferred pending the §32 decisions.

### Critical Questions — Explicit Answers

1. **Does CarbonTally currently support customer-owned factors?**
   **No.** No customer-factor domain, table, repository, API, or RLS exists in
   v2.1 or the legacy app. All factors are CarbonTally-managed (`emission_factors`
   / `defra_conversion_factors`).
2. **Does CarbonTally currently store customer-supplied factor values?**
   **No.** `emissions_logs` stores a CarbonTally `emission_factor_id` and the
   computed `calculated_kg_co2e`; customer-supplied values are never read or
   stored (legacy CSV path overwrites them; manual entry passes a DEFRA id).
3. **Can a customer currently select a CarbonTally factor manually?**
   **Partially (legacy only).** Legacy manual entry maps a selected
   `fuel_utility_type` to a DEFRA factor and stores `defra_factor_id`; v2.1
   `POST /api/v2/calculate` accepts an explicit `factor_id`. There is no v2.1
   customer "factor dropdown" API.
4. **Is that selection currently validated?**
   **Legacy: no** (`POST /api/emissions` trusts `defra_factor_id` + client-computed
   `calculated_kg_co2e`). **v2.1: existence + unit only** (factor resolved through
   `EmissionFactorsRepository`; `UnitMismatchError` on unit mismatch).
5. **Can customer factors be stored without modifying the global
   `emission_factors` table?**
   **Yes** — a dedicated `customer_factors` table requires zero changes to
   `emission_factors`, its natural key, or its RLS.
6. **Should customer factors have a dedicated table?**
   **Yes.** `emission_factors` is global authenticated-read reference data with a
   non-org natural key; extending it breaks the global model and raises leak
   risk (§10). The `factor_aliases` org-scoped pattern is the precedent.
7. **Can customer factors be incorporated into the existing Factor Matching
   Engine?**
   **Yes — by extension.** The pipeline is candidate-set-agnostic; customer
   factors enter as an injected candidate source with customer-first precedence,
   no stage rewrite (§15).
8. **Can customer factors be incorporated into the existing Calculation Engine?**
   **Yes — by extension.** The math/unit-check/snapshot/verify logic is
   ownership-agnostic; the factor is an `EmissionFactor`-shaped object with
   `factor_source='CUSTOMER'`. The only obstacle is the snapshot FK (§16).
9. **Can calculation snapshots preserve customer-factor provenance?**
   **Yes** (after §16 O1/O2). Snapshots already freeze factor_id + multiplier +
   `factor_source`/`factor_set`/`import_batch_id`; a customer factor uses
   `factor_source='CUSTOMER'`, `import_batch_id=NULL`, and a `customer_factor_id`
   reference. Historical snapshots never change (§12).
10. **Can RLS isolate customer factors?**
    **Yes.** Reuse `is_org_member()` in new `customer_factors` policies
    (select/insert/update/delete), mirroring `factor_aliases`. This is the one
    required RLS change set (§19).
11. **Can consultants access customer factors according to their existing
    organisation permissions?**
    **Yes — with a caveat.** If consultants are `organization_members` of the
    client org, `is_org_member` covers them; if access is via
    `consultant_clients` only, the policy needs a consultant clause
    (**INVESTIGATE**, R3/D-cf-6).
12. **What is the minimum database change?**
    One new table (`customer_factors`) + its RLS policies + the
    `calculation_snapshots` FK resolution (O1). **No change** to `emission_factors`
    (7,049 factors), its natural key, or its RLS (§30).
13. **What is the minimum backend change?**
    `CustomerFactor` domain type + `CustomerFactorsRepository` + candidate-merge
    in matching + customer-factor branch in calculation + validation extension.
    No second engine (§28).
14. **What is the minimum API change?**
    ~7 additive customer-factor routes + extended `factor-match` (customer
    candidates) + extended `calculate` (`customer_factor_id`, org-checked) +
    `CalculationSnapshotOut` provenance exposure. Existing 19 contracts
    unchanged (§24).
15. **What should NOT be changed?**
    `emission_factors` (data, schema, RLS, natural key); the 7,049 factors;
    matching/calculation math; the 19 v2.1 route contracts; the error envelope;
    the immutable-snapshot + content-hash machinery; legacy
    `defra_conversion_factors`/`POST /api/emissions`/`ManualEntryStandalone`;
    and nothing that would create a duplicate engine/approval/snapshot system
    (§29).

---

<!-- TM_CF_END -->

---
### Audit scope and verification

- Read-only: no source, DB, migration, RLS, Storage, API, frontend or test
  changes were made.
- Evidence traced: `backend/api/contracts.py`, `engines/calculation.py`,
  `engines/factor_matching.py`, `infra/search_index.py`, `data/emissions_logs.py`,
  legacy `backend/routes/emissions.py`, `backend/routes/reference.py`,
  `backend/process_emissions.py`, `frontend/src/components/ManualEntryStandalone.jsx`,
  `frontend/src/App.js` (CSV import), `supabase/migrations/00000000000000_init_schema.sql`
  (approval_requests/approval_decisions/customer_verifications),
  `20260807070000_add_new_table_rls.sql` (aliases/snapshot policies, is_org_member),
  `20260807000000_add_import_batches.sql`, `20260807050000_add_factor_aliases.sql`,
  RC1/RC2 reference-table RLS manifest, legacy storage conventions.
- Open flags: consultant membership model (R3), approval authority (D-cf-3),
  factor precedence (D-cf-5), snapshot FK option (D-cf-2).
