# CarbonTally V3 — Terminology & Domain Glossary

| | |
|---|---|
| Document type | Domain terminology reference |
| Project | CarbonTally |
| Architecture | CarbonTally V3 (layered: api → engines → domain → data → infra) |
| Version | 1.0 |
| Status | AUTHORITATIVE-TO-IMPLEMENTATION (no application code changed) |
| Created | 2026-08-20 |
| Author | Cline |

## 0. Purpose, method and authority rule

This glossary defines every term used across the CarbonTally V3 codebase,
database, API, frontend, the V3 audit reports and the local demo-user
implementation, and records the **authoritative meaning derived from the
existing implementation**.

**Authority rule.** Where docs and code disagree, the *implementation* wins.
Precedence, highest first:

1. **Database schema** — CHECK constraints and foreign keys in
   `supabase/migrations/*.sql` (verbatim vocabularies; e.g. the org-role
   vocabulary is the `organization_members.role` CHECK).
2. **Domain constants** — `backend/core/types.py`, `backend/domain/*.py`
   (e.g. `Scope`, `ITEM_STATUSES`, `BATCH_STATUSES`, `WORKFLOW_STAGES`,
   `ISSUE_TYPES`, `STAFF_PERMISSION_KEYS`).
3. **API contracts** — `backend/api/*.py` (e.g. `REPORT_STATUSES`,
   `SUPPORTED_REPORT_TYPES`, `CONSULTANT_PERMISSIONS`).
4. **RLS policies** — `supabase/migrations/*_rls.sql` (e.g. org-admin = role
   IN `('owner','admin')`).
5. **Frontend labels** — `frontend/src/v3/**` (display vocabulary).
6. **V3 audit reports** — `docs/audit/cline/CARBONTALLY_V3_*` and
   `docs/architecture/*` (historical/planning intent only).

Terms that are ambiguous or in conflict across these sources are **flagged
`[CONFLICT — FOR HUMAN DECISION]`** and listed in §15. No code, schema or
config was changed to produce this document.

---

## 1. Identity, roles and access control

### 1.1 Organisation roles (`organization_members.role`)
- **Schema-authoritative vocabulary** (CHECK constraint):
  `owner | admin | member | viewer`.
- Meaning:
  - `owner` — the organisation owner; admin of its own org. The RLS admin
    policies (`om_insert_admin`, `om_update_admin`, `om_select_self_or_admin`)
    treat `role IN ('owner','admin')` as org administrators, and
    `require_org_admin` recognises `owner` (P1-F4).
  - `admin` — organisation administrator (same RLS admin rights as owner).
  - `member` — ordinary active member (can read org data, cannot administer).
  - `viewer` — read-only access to the organisation's data.
- **Derived `AuthUser.role` forms** (from `auth.py get_current_user`):
  `org_owner`, `org_admin`, `org_member`/`org_viewer` — the same membership
  roles prefixed with `org_`. `[CONFLICT — FOR HUMAN DECISION: two spellings
  of the same concept; §15.1]`.

### 1.2 Staff model (`staff_profiles`, `staff_roles`, `roles`)
- `staff_profiles` — CarbonTally workforce row. FK `role_id → staff_roles.id`.
  `entity_id IS NULL` = **CarbonTally internal staff**; `entity_id` populated =
  **processing-entity staff** (ADR-V3-001 Q5 positive NULL convention).
- `staff_roles` — the authoritative staff-role vocabulary table. Carries the
  `permissions` jsonb resolved via `staff_profiles.role_id` (P1-F2 pointed the
  ops path at this table).
- `roles` — the **customer-org role reference** table (invitation `role_id`
  resolution / `/api/v3/organizations/{id}/roles`). Not the staff permission
  source. `[CONFLICT — FOR HUMAN DECISION: two "roles" tables; §15.2]`.
- Staff role names in use (local demo seed): `operator`, `reviewer`,
  `qc_specialist`, `admin`.

### 1.3 Staff permissions (the `can_*` vocabulary)
- Reference vocabulary `STAFF_PERMISSION_KEYS` (`backend/domain/staff.py`) and
  `DEFAULT_STAFF_PERMISSIONS` (`backend/auth.py`): `can_view_all`,
  `can_manage_staff`, `can_manage_roles`, `can_view_organizations`,
  `can_manage_organizations`, `can_extract`, `can_process`, `can_review`,
  `can_approve`, `can_export`, `can_delete`.
- Phase 8 ops gates use a subset: `can_view_all` (dashboard),
  `can_process` (data entry / operator), `can_review` (review/QC),
  `can_manage_staff` (staff/assignment admin) — see `PERMISSION_DASHBOARD`
  etc.
- `[CONFLICT — FOR HUMAN DECISION: `can_view_all` vs `can_view_organizations`
  overlap; §15.9]`.

### 1.4 Consultant model
- `consultant_profiles` — a consultant firm (owner = the firm's primary user).
- `consultant_firm_members` — firm team members; display `role` vocabulary
  `CONSULTANT_ROLES = ("owner", "manager", "consultant", "viewer")`; the
  **actual authorization surface** is the `can_*` boolean columns
  (`can_manage_clients`, `can_upload_documents`, `can_generate_reports`,
  `can_manage_team`) plus `client_access uuid[]`.
- `consultant_clients` — a firm↔organisation grant; `status` vocabulary
  `CLIENT_STATUSES = ("active", "inactive")`.

### 1.5 CarbonTally admin / require_admin
- `auth.py require_admin()` — satisfied when `AuthUser.role`/`role_name` is
  `admin`. Since P1-F3, staff admins resolve `role_name` from `staff_roles`
  (a `staff_roles.name = 'admin'` row). Guards the `/api/v3/qc/*` surface.

### 1.6 Auth user derived roles
- `user` — default (authenticated but not staff/org-member).
- `staff` — fallback when a staff profile has no resolvable role name.
- `admin` — global/staff administrator (role_name from `staff_roles`).
- `org_*` — org membership derived roles (see §1.1).

---

## 2. Organisations and tenancy

- `organizations` — the tenant root. Key fields: `name`, `country`,
  `currency`, `reporting_standard`, `financial_year_end`,
  `default_factor_year`, `subscription_status`, `subscription_tier`.
- `organization_metadata` — one-to-one org intensity/ESG metadata
  (FTE, revenue, floor area, renewable percentage, …).
- `organization_members` — org↔user membership (see §1.1). RLS helpers
  `is_org_member(org)`, `is_org_consultant(org)` gate every tenant table.
- Tenancy scoping: every V3 repo SQL is org-scoped; RLS additionally enforces
  `is_org_member` / `is_org_consultant`.

## 3. Facilities, assets, suppliers

- `facilities` — physical sites (CHECK: `country IN ('GB','IE')`; postcode or
  eircode required). Free-text `type` (demo: `production`, `office`,
  `warehouse`). `[CONFLICT — FOR HUMAN DECISION: no type CHECK; §15.10]`.
- `assets` — equipment/vehicles at a facility (`facility_id` FK). Free-text
  `type` (demo: `boiler`, `vehicle`, `equipment`).
- `suppliers` — org suppliers. `supplier_category_id` →
  `supplier_categories`; optional reported emissions
  (`annual_emissions_scope1..3`). Free-text `type` (demo: `electricity`,
  `natural_gas`, `freight`).

## 4. Documents and files

- **Two document stores** (both authoritative; different roles):
  - `organization_files` — the **upload/browse document record** written by
    the V3 upload path (`POST /api/v3/uploads` → Supabase Storage + row).
    Fields: `path`, `size_bytes`, `file_type`, `mime_type`, `bucket`,
    `status`, `metadata`.
  - `customer_documents` — the **legacy customer document** row
    (`status` CHECK: `uploaded|pending|processing|processed|manual_review|
    verified|approved|rejected|failed`). `[CONFLICT — FOR HUMAN DECISION: two
    document entities with overlapping purpose; §15.3]`.
- `file_type` (classifier in `api/v3_documents.py`):
  `PDF | IMAGE | SPREADSHEET | OTHER` — derived from filename extension/mime.
- `upload_batches` — a **grouping of uploads** (a batch of files). Columns
  `total_files`, `processed_files`, `status`; `manual_extraction_requested`,
  `manual_extraction_batch_id` link into the manual-extraction pipeline.
  `[CONFLICT — FOR HUMAN DECISION: "batch" is overloaded; §15.4]`.


## 5. Processing and extraction workflow

### 5.1 Work order entities
- `manual_extraction_batches` — a **manual-extraction work order** created by
  an org admin; `status` vocabulary `BATCH_STATUSES`
  (`open|in_progress|qc_in_progress|qc_passed|completed|cancelled|failed`).
- `manual_extraction_items` — a **document within a manual-extraction batch**;
  `status` vocabulary `ITEM_STATUSES`
  (`pending|extracting|extracted|mapping|mapped|validating|validated|
  calculating|calculated|customer_review|approved|rejected|qc_approved|
  qc_rejected|failed`).
- `processing_queue` — legacy queue rows (`queue_status` CHECK:
  `pending|assigned|in_progress|on_hold|completed|cancelled`).
- `document_processing_queue` — legacy per-document AI-extraction queue
  (`status` CHECK:
  `pending|processing|ai_extracted|manual_review|manual_extraction|qc|
  customer_review|approved|rejected|completed|failed`).
- `manual_review_queue` — the **internal review queue** (assignments, SLA).
  Statuses in use (code/demo): `pending`, `assigned`, `in_review`,
  `completed`.

### 5.2 Workflow stages (`WORKFLOW_STAGES`)
- `source → extraction → mapping → validation → calculation → review →
  approval`; QC (`qc_approved`/`qc_rejected`) is an orthogonal staff gate
  applied to `extracted` items. Stage→status mapping is
  `WORKFLOW_STAGE_STATUSES`.
- `[CONFLICT — FOR HUMAN DECISION: `manual_review_queue.status` uses a
  different vocabulary from `manual_extraction_items.status`, yet both drive
  "review" work; §15.6]`.

### 5.3 Issues
- `issues` — first-class issues (ADR-V3-009, Option B). Vocabulary:
  `ISSUE_TYPES = ("defect","exception","escalation")`,
  `ISSUE_SEVERITIES = ("low","medium","high","critical")`,
  `ISSUE_STATUSES = ("open","in_progress","on_hold","escalated","resolved",
  "closed")`.
- Context FKs: `organization_id`, `entity_id` (→ `processing_entities`),
  `work_item_id` (→ `manual_review_queue`), `document_id` (→
  `customer_documents`), `batch_id` (→ `upload_batches`).
  `[CONFLICT — FOR HUMAN DECISION: `work_item_id` is ambiguous (see §15.5); in
  the ops manual-extraction path it is intentionally NULL (P1-F2) because
  manual-extraction items are not `manual_review_queue` rows]`.

## 6. Emissions and calculation

- `emission_factors` — the authoritative factor catalogue (7,049 rows
  locally). Columns: `reporting_year`, `activity_type`, `co2e_multiplier`,
  `unit`, `scope`, `factor_source`, `factor_set`, `country` (CHECK `GB|IE`),
  `import_batch_id`.
- `factor_source` — provider label (e.g. `DEFRA-DESNZ`, `SEAI`).
- `factor_set` — dataset/year label (e.g. `DEFRA-2025`).
- `calculation_snapshots` — immutable calculation record (ADR-5/ADR-V3-005):
  `activity`, `activity_type`, `quantity`, `quantity_unit`, `co2e_multiplier`,
  `co2e_kg`, `scope`, `factor_id`/`customer_factor_id`, `factor_kind`
  (`emission_factor`|`customer_factor`), `content_hash`, `reporting_year`,
  `methodology` (`direct_multiply`), `algorithm_version`.
- `emissions_logs` — the org's emissions rows consumed by exports/reports:
  `raw_quantity`, `calculated_kg_co2e`, `start_date`/`end_date`, `unit`,
  `scope`, `emission_factor_id`, `snapshot_id`, `supplier_id`,
  `organization_member_id`, `data_source` (free-text; demo uses `utility`,
  `manual`; the calculate API writes its own source). `[CONFLICT — FOR HUMAN
  DECISION: `data_source` has no CHECK; §15.10]`.
- **Scope vocabulary** (`core/types.py Scope`):
  `Scope 1 | Scope 2 | Scope 3 | Outside of Scopes`.
  Legacy client alias `scope1|scope2|scope3` is normalised to canonical at the
  `POST /api/v3/emissions/calculate` boundary (P1-F5). `[CONFLICT — FOR HUMAN
  DECISION: legacy aliases may still exist in older data/clients; §15.7]`.
- `customer_factors` — org-specific factors; `status` CHECK:
  `draft|active|inactive|archived`; matched ahead of the global catalogue per
  ADR-V3-002 (D-cf-5).

## 7. Reporting

- `report_generation_queue` — report lifecycle rows. **V3 API status
  vocabulary** `REPORT_STATUSES = ("pending","generating","completed",
  "failed")` with display labels `Queued | Generating | Ready | Failed`.
  `[CONFLICT — FOR HUMAN DECISION: the legacy claim index and some docs use
  `queued`/`processing`; the table has no status CHECK; §15.8]`.
- `report_type` — the V3 engine supports exactly **`annual`**
  (`SUPPORTED_REPORT_TYPES`); legacy generator labels (`summary`, `documents`,
  `staff`, …) are not V3 engine-backed. `[CONFLICT — FOR HUMAN DECISION:
  legacy report-type labels differ from V3; §15.11]`.
- `generated_content` — jsonb `{page_count, content:{…12 sections…}}`.
- `report_versions` — version snapshots (`version_number`, `is_current`,
  `content`, `file_url`, `change_summary`).
- Exports (`/api/v3/exports/*`): `emissions.csv`, `emissions.json`,
  `documents.csv` — read-only over `emissions_logs`/`organization_files`.


## 8. Consultants and clients
- See §1.4. `consultant_tasks` — tasks under a firm (`task_type`, `priority`,
  `status` — free-text). The consultant dashboard derives `clients_by_status`,
  `pending_reviews`, `open_issues`, `ready_reports` from real rows
  (consultant_clients, manual_review_queue, issues, report_generation_queue).

## 9. Processing entities
- `processing_entities` — CarbonTally processing companies; `status` CHECK:
  `active|remediation|suspended|terminated`. Entity staff are scoped to their
  own entity via `staff_profiles.entity_id` and the RLS/guard
  `is_entity_member` (ADR-V3-001).

## 10. Accounts, subscriptions, beta
- `customer_subscriptions.status` CHECK: `trialing|active|past_due|paused|
  cancelled|expired`. `organizations.subscription_status`/`subscription_tier`
  mirror this at the org level. `[CONFLICT — FOR HUMAN DECISION: two
  subscription vocabularies; §15.12]`.
- `beta_access_codes` / `beta_users` — legacy invite/beta management.
- `import_batches` — factor dataset imports; `status` CHECK:
  `pending|importing|completed|failed|rolled_back`.

## 11. Frontend surface terms (V3)
- Primary nav (`V3Layout`): **Dashboard · Emissions · Documents · Processing ·
  Reports · Organization · Consultant · Operations** (+ context badges
  `Staff` / `Consultant`).
- Ops tabs: **Dashboard · Data entry · Review · QC · Staff**.
- Consultant hub: **Consultant dashboard · Client workspace · Clients ·
  Client switching** (active client shown as "CURRENT ORGANIZATION").
- Report status labels: `pending→Queued`, `generating→Generating`,
  `completed→Ready`, `failed→Failed`.
- Upload `data_type` (form): `utility | fuel | scope3 | other`.
- Page names: `/home` (Dashboard), `/emissions`, `/documents`, `/processing`,
  `/reports`, `/reports/:id`, `/organization`, `/consultant`, `/ops`.

## 12. API generations and architecture references
- **Legacy surface** — `/api/*` routes (`routes/**`) served by `main.py`;
  includes the legacy monolith frontend calls.
- **V2 surface** — `/api/v2/*` (`api/router.py`, `main_v2.py`); health +
  admin + engine surfaces (`/api/v2/factor-match` etc.).
- **V3 surface** — `/api/v3/*` (customer admin, documents/uploads, emissions,
  exports, consultants, ops, manual-extraction, processing, QC, reports,
  suppliers, issues, customer-factors, verifications, notifications).
  `[CONFLICT — FOR HUMAN DECISION: the "v2" router tag is "CarbonTally v2.1"
  yet the same `api/router.py` mounts the `v3_*` routers; two entry points
  `main.py` vs `main_v2.py` still coexist (conformity gate); §15.13]`.
- Architecture decision registers referenced throughout: **ADR-V3-001**
  (processing entities), **ADR-V3-002** (customer factors), **ADR-V3-004**
  (no worker infra; synchronous pipeline), **ADR-V3-005/ADR-5**
  (calculation snapshots), **ADR-V3-009** (issues), and the **CT-ARCH-***
  rules (e.g. CT-ARCH-009 stateless engines, CT-ARCH-012, CT-ARCH-014).

## 13. Local demo implementation terms
- Demo organisation: **CarbonTally Demo Ltd** (`11111111-1111-4111-8111-111111111111`).
- Demo auth identities (`*@demo.carbontally.local`), mapped in
  `local_backups/mint_tokens.py` and `local_backups/seed_demo_data.sql`:
  - Org members: `owner`/`admin`/`member`/`viewer` (real
    `organization_members.role`).
  - Staff: `operator` (can_process), `reviewer` (can_review),
    `qc_specialist` (can_process+can_review), `admin` (full ops perms) —
    seeded as `staff_roles` rows.
  - Consultant firm: **Net Zero Advisory Ltd** with one firm member (owner)
    and one client grant on the demo org.
- Demo data uses the real `emission_factors` (DEFRA-DESNZ) and canonical scope
  values (`Scope 1|2`) after P1-F5.


## 14. Status vocabularies index (status is always table-scoped)

There is **no single shared status enum**; each table/aggregate owns its
vocabulary. The authoritative sets in use:

| Scope | Vocabulary | Source |
|---|---|---|
| `organization_members.role` | `owner, admin, member, viewer` | schema CHECK |
| `customer_documents.status` | `uploaded, pending, processing, processed, manual_review, verified, approved, rejected, failed` | schema CHECK |
| `document_processing_queue.status` | `pending, processing, ai_extracted, manual_review, manual_extraction, qc, customer_review, approved, rejected, completed, failed` | schema CHECK |
| `processing_queue.queue_status` | `pending, assigned, in_progress, on_hold, completed, cancelled` | schema CHECK |
| `customer_subscriptions.status` | `trialing, active, past_due, paused, cancelled, expired` | schema CHECK |
| `import_batches.status` | `pending, importing, completed, failed, rolled_back` | schema CHECK |
| `processing_entities.status` | `active, remediation, suspended, terminated` | schema CHECK |
| `customer_factors.status` | `draft, active, inactive, archived` | schema CHECK |
| `issues.issue_type` | `defect, exception, escalation` | schema CHECK + domain |
| `issues.severity` | `low, medium, high, critical` | schema CHECK + domain |
| `issues.status` | `open, in_progress, on_hold, escalated, resolved, closed` | schema CHECK + domain |
| `manual_extraction_batches.status` | `open, in_progress, qc_in_progress, qc_passed, completed, cancelled, failed` | `BATCH_STATUSES` (domain) |
| `manual_extraction_items.status` | `pending, extracting, extracted, mapping, mapped, validating, validated, calculating, calculated, customer_review, approved, rejected, qc_approved, qc_rejected, failed` | `ITEM_STATUSES` (domain) |
| workflow stages | `source, extraction, mapping, validation, calculation, review, approval` | `WORKFLOW_STAGES` (domain) |
| `consultant_clients.status` | `active, inactive` | `CLIENT_STATUSES` (domain) |
| `report_generation_queue.status` (V3) | `pending, generating, completed, failed` | `REPORT_STATUSES` (api) |
| scope values | `Scope 1, Scope 2, Scope 3, Outside of Scopes` | `core.types.Scope` |
| `emissions_logs.scope` / `calculation_snapshots.scope` | canonical scope values (aliases `scope1..3` normalised at the API) | `Scope` + P1-F5 |
| `calculation_snapshots.factor_kind` | `emission_factor, customer_factor` | domain/schema CHECK |
| `organization_files.status` (used) | `uploaded, pending, processing, processed, verified, approved, rejected, failed` (no CHECK) | repo usage |
| `manual_review_queue.status` (used) | `pending, assigned, in_review, completed` (no CHECK) | repo/demo usage |
| upload `data_type` | `utility, fuel, scope3, other` | frontend form + upload API |
| `organization_files.file_type` | `PDF, IMAGE, SPREADSHEET, OTHER` | `api/v3_documents.py` classifier |


## 15. AMBIGUOUS / CONFLICTING TERMS — FOR HUMAN DECISION

The following terms are ambiguous or conflict across the documentation and the
implementation. No unilateral decision was made; each needs a human decision.

### 15.1 `owner` vs `org_owner` / `admin` vs `org_admin`
- `organization_members.role` stores `owner`/`admin` (schema). `AuthUser.role`
  derives `org_owner`/`org_admin` (auth.py). `require_org_admin` accepts both
  spellings (P1-F4). Docs use both interchangeably.
- **Decision needed:** pick one canonical spelling for the domain (the schema
  values are the natural candidates); keep the derived `org_*` form internal
  to auth.

### 15.2 Two "roles" tables: `roles` vs `staff_roles`
- `staff_profiles.role_id → staff_roles.id` (FK) — staff permission source.
  `roles` is the org-role reference (invitation resolution) and is effectively
  unused for RBAC. Historical docs/`auth.py` docstrings still say staff
  permissions come from `roles.permissions` (contradicted by the schema).
- **Decision needed:** confirm `roles` remains the org-role catalog; decide
  whether to retire/repurpose it or add a CHECK vocabulary.

### 15.3 Two document entities: `organization_files` vs `customer_documents`
- V3 uploads write `organization_files`; the legacy surface uses
  `customer_documents`. Both have a `status` column with different
  vocabularies. RLS `is_org_member`/`is_org_consultant` applies to both.
- **Decision needed:** is `customer_documents` a deprecated parallel store, or
  are they intentionally distinct (upload record vs processed document)?

### 15.4 Overloaded "batch"
- `upload_batches` (grouping of uploads), `manual_extraction_batches`
  (manual-extraction work order), and `issues.batch_id` →
  `upload_batches` (not manual-extraction batches). The word "batch" appears
  in all three.
- **Decision needed:** adopt disambiguating labels (e.g. "upload batch",
  "extraction batch") in docs/UI where the ambiguity matters.

### 15.5 Ambiguous "work item"
- `issues.work_item_id` FKs to `manual_review_queue`. In the ops
  manual-extraction path it is NULL (P1-F2) because manual-extraction items
  are not review-queue rows. Some docs use "work item" to mean any processing
  item.
- **Decision needed:** define "work item" precisely (review-queue row only, or
  any extractable document?).

### 15.6 Review vocabulary conflict
- `manual_review_queue.status` (`pending/assigned/in_review/completed`) vs
  `manual_extraction_items.status` (`customer_review`, `review` stage) vs
  `document_processing_queue.status` (`manual_review`). Three different
  "review" states.
- **Decision needed:** document the three review concepts explicitly
  (staff-review queue, customer-review stage, legacy review state).

### 15.7 Scope aliases vs canonical scope
- Legacy clients/frontend sent `scope1|scope2|scope3`; the canonical
  vocabulary is `Scope 1|Scope 2|Scope 3|Outside of Scopes`. P1-F5 normalises
  at the API boundary, but old rows/clients may still carry aliases.
- **Decision needed:** formally deprecate the aliases (reject at the boundary
  rather than normalise) or keep normalising for backward compatibility.

### 15.8 Report status vocabulary
- V3 API/UI: `pending, generating, completed, failed` (labels
  Queued/Generating/Ready/Failed). Legacy claim index and some docs use
  `pending, queued, processing`. The table has no status CHECK.
- **Decision needed:** ratify `pending|generating|completed|failed` as the
  single vocabulary and add a CHECK (schema change — defer to Phase 9).

### 15.9 Overlapping staff permissions
- `can_view_all` (ops dashboard) vs `can_view_organizations` (org visibility);
  `can_process` vs `can_extract`. Both pairs overlap in intent.
- **Decision needed:** confirm the Phase 8 subset
  (`can_view_all, can_process, can_review, can_manage_staff`) as the
  authoritative operational set and document the rest as legacy.

### 15.10 Free-text vocabularies (no CHECK)
- `facilities.type`, `assets.type`, `suppliers.type`,
  `emissions_logs.data_source`, `report_type` (legacy labels),
  `consultant_tasks.status`, `organization_files.status`.
- **Decision needed:** which of these should become CHECK-constrained /
  enum-driven (schema change — defer to Phase 9).

### 15.11 Report types
- V3 engine supports only `annual`; legacy labels (`summary`, `documents`,
  `staff`, …) exist in the legacy generator. The V3 reports UI offers only
  `annual`.
- **Decision needed:** confirm `annual` as the only V3 report type and that
  legacy labels are retired with the legacy surface.

### 15.12 Two subscription vocabularies
- `customer_subscriptions.status` (CHECK) vs
  `organizations.subscription_status` (free-text mirror).
- **Decision needed:** single source of truth (subscriptions table vs org
  column).

### 15.13 API surface generations / entry points
- `main.py` (legacy + mounts v2.1 router with v3 routers) vs `main_v2.py`
  (v2.1 app only); `/api/*` (legacy), `/api/v2/*`, `/api/v3/*` all coexist.
  The conformity gate lists entry-point consolidation as a condition.
- **Decision needed:** consolidation plan + deprecation of `/api/*`.


## 16. Alphabetical term index

| Term | Section |
|---|---|
| admin (org role / staff role / AuthUser) | §1.1, §1.2, §1.5, §1.6 |
| approved / rejected (multi-context) | §5.1, §5.3, §14 |
| batch (overloaded) | §4, §5.1, §15.4 |
| BATCH_STATUSES | §5.1, §14 |
| calculation_snapshots | §6, §14 |
| can_* permissions | §1.3, §15.9 |
| CarbonTally internal staff | §1.2, §9 |
| CLIENT_STATUSES | §1.4, §14 |
| consultant_clients / firm / profiles | §1.4, §8 |
| content_hash | §6 |
| customer_documents | §4, §15.3 |
| customer_factors | §6, §14 |
| data_source | §6, §15.10 |
| document_processing_queue | §5.1, §14 |
| emission_factors | §6 |
| emissions_logs | §6, §14 |
| exports | §7 |
| facilities / assets / suppliers | §3, §15.10 |
| factor_kind / factor_set / factor_source | §6 |
| file_type | §4, §14 |
| import_batches | §10, §14 |
| is_org_member / is_org_consultant | §2 |
| issues | §5.3, §14, §15.5 |
| ITEM_STATUSES | §5.1, §14 |
| manual_extraction_batches / items | §5.1, §14 |
| manual_review_queue | §5.1, §14, §15.6 |
| member (org role vs firm member) | §1.1, §1.4 |
| organization_files | §4, §14 |
| organization_members / organizations | §1.1, §2 |
| owner / org_owner | §1.1, §15.1 |
| processing entities | §1.2, §9, §14 |
| processing_queue | §5.1, §14 |
| QC (gate vs admin surface) | §5.2, §1.5 |
| report_generation_queue | §7, §14, §15.8 |
| report_type / annual | §7, §15.11 |
| report_versions | §7 |
| reviewer / review (staff vs customer vs legacy) | §1.2, §5.2, §15.6 |
| roles vs staff_roles | §1.2, §15.2 |
| scope (Scope 1..3, Outside of Scopes) | §6, §14, §15.7 |
| staff_profiles / staff_roles | §1.2 |
| upload_batches | §4, §15.4 |
| viewer (org vs firm) | §1.1, §1.4 |
| work item | §5.3, §15.5 |
| WORKFLOW_STAGES / WORKFLOW_STAGE_STATUSES | §5.2, §14 |

---

*End of glossary. Authority: implementation (schema → domain → API → RLS →
frontend → docs). Terms flagged `[CONFLICT — FOR HUMAN DECISION]` are listed
in §15 and require a human decision before any schema/documentation
consolidation.*

