# CarbonTally — Storage Management PO Evidence Review (Q1–Q10)

* **Task:** CarbonTally Storage Management — PO target-decision stage
* **Date:** 2026-09-30
* **Repository:** `/home/shomonrobie/ct_93d5cdd`
* **Nature of this artefact:** **read-only evidence report.** No code, test, migration,
  schema, configuration, bucket, object or policy was created, altered or removed.
* **Provisional input under review (NOT evaluated as decided):**
  `consultant/{CONSULTANT_ID}/client/{CLIENT_ID}/...`
* **Final status:** `STORAGE PO EVIDENCE REVIEW COMPLETE — READY FOR PO REVIEW`

---

## 0. Scope, method and read-only declaration

### 0.1 Governance observed

| Rule | How it was observed |
|---|---|
| Read-only investigation only | Only `SELECT`-class SQL and file reads were performed. |
| No source/test/migration/schema/config change | `git status --porcelain` at the end of the task shows exactly one new file: this report (§10.4). |
| No database/Supabase modification | All SQL executed was `SELECT`/catalogue inspection. No DDL, DML, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `GRANT` or bucket call was issued. |
| No bucket/object creation, movement or deletion | No Supabase Storage API call was made by this review. |
| Evidence labelling | Every finding below is labelled `EXISTING DECISION`, `IMPLEMENTED BEHAVIOUR`, `DOCUMENTED INTENT`, `CODE-TRACED`, `INFERENCE`, `CONFLICTING EVIDENCE`, `NOT ESTABLISHED`, or `UNVERIFIED`; live-probe facts are labelled `LIVE — READ-ONLY VERIFIED`. |
| No invented PO decision / no industry assumption | Undecided items are reported as `NOT ESTABLISHED` and carried into §8. |
| Documents vs code disagreement | Reported in §7, never reconciled. |
| Baseline not treated as authoritative | `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md` was used only as an evidence index; every baseline claim cited here was re-verified against the underlying migration, schema, code or live catalogue. Where this review re-verified a baseline claim, the underlying source is cited, not the baseline. |

### 0.2 Environments probed

| Label | Target | Access | Nature |
|---|---|---|---|
| `ENV-LOCAL` | `ct_local_93d5cdd` (disposable local cluster; `backend/.env: DATABASE_URL`) | `psql`, read-only | `LIVE — READ-ONLY VERIFIED` |
| `ENV-LIVE` | `SUPABASE_LIVE_POSTGRES_DATABASE_URL` (pooler DSN in `backend/.env`) | `psql`, read-only, `statement_timeout = 15s` | `LIVE — READ-ONLY VERIFIED` |

Probe statements issued (read-only): `pg_indexes`, `pg_policies`, `pg_constraint`,
`information_schema.columns`, `storage.buckets`, `storage.objects` aggregate counts, and
`count(*)`/`count(DISTINCT …)` aggregates on `public.consultant_clients`. No row-level data
was read or recorded; the report contains counts and identifiers, never secrets.

### 0.3 Question set and headline answers

| Q | Headline answer from existing evidence |
|---|---|
| Q1 | **YES — established at the data/permission level**, with no exclusivity and no handover workflow. One client organisation may hold simultaneous grants from more than one consultant firm. |
| Q2 | **ESTABLISHED — the client organisation is the data owner.** The consultant firm is explicitly *never* the data owner; the uploader is provenance only. |
| Q3 | **Access revocation only** is decided and implemented. Object deletion / movement / archival / reassignment on revocation is **NOT ESTABLISHED**. |
| Q4 | **No customer-vs-consultant physical distinction exists today** (both write one shared org-scoped prefix). **No** `customer/…` or `consultant/…` namespace is established anywhere. |
| Q5 | **Conditionally allowed in the application layer, denied in the storage layer** — a real, unresolved asymmetry (§6.2). |
| Q6 | **Yes, in practice** — consultant-uploaded documents are indistinguishable from customer uploads and are readable by the client organisation's members. |
| Q7 | **NOT ESTABLISHED** — no content-hash / dedupe identity exists for documents or objects. |
| Q8 | **Fully decided and ratified** (`B4-D5/D6/D7`): private `report-artifacts`, key `{organization_id}/{report_id}/{version_id}.pdf`, SHA-256, append-only, **no consultant id**. |
| Q9 | **Organisation-level** entitlement is decided and implemented; consultant-firm-level storage quota is **NOT ESTABLISHED**. |
| Q10 | Deletion/retention/audit/signed-URL answers are mixed: see the classification table in §3.3. |

---

## 1. Executive Summary

### 1.1 What existing CarbonTally evidence already establishes (do not re-decide)

1. **A client organisation may be served by more than one consultant firm.** The relationship
   table `public.consultant_clients` carries `UNIQUE (consultant_id, organization_id)` — i.e. the
   uniqueness is on the *pair*, and there is **no** uniqueness or exclusivity on
   `organization_id` alone. `LIVE — READ-ONLY VERIFIED` in both probed environments. Two
   architecture documents state the consequence explicitly:
   * `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §37.3: *"Multiple consultant
     grants to one org **are schema-representable** (`UNIQUE(consultant_id, organization_id)`), so
     'client chooses another consultant' is data-representable, but there is no API/frontend flow and
     no exclusivity or handover enforcement."*
   * `docs/architecture/CARBONTALLY_P6_2F_INDEPENDENT_VERIFICATION_REPORT.md` finding **IV-N2**:
     *"Where two firms both hold active grants for the same organisation, both are notified about an
     item one firm worked on."*
   The *approved direction* for the lifecycle (§37.4, "APPROVED direction — NOT implemented") includes
   branch **(c) "Client chooses another consultant (new grant; handover)"**.
2. **Business ownership is the client organisation — absolutely.** Ratified in the P17 decision
   record (`docs/architecture/CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925.md`
   rows 9–11): *"Data ownership remains with the client organization"*, *"Operator/actor identity
   remains distinct from data ownership"*, *"Reports, evidence and calculations belong to the owning
   organization even when prepared by a consultant"* (source decision **D2 §24**: *"The report belongs
   to ABC's accounting context, not the consultant's organization."*), extended to *"calculations,
   evidence, activity data, reporting versions, reportability, audit history"*. The consultant
   relationship row is classified *"consultant-contextual … **never the data owner**"*
   (`CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §37.5). Consultant access is *"delegated and
   client-specific"* and *"client-org data ownership and isolation are absolute"*
   (`CT-PO-P17-ARCH-01-…-20250925.md` §57.1 row 7).
3. **Revocation is an access decision, not a data decision.** D15 (APPROVED 2026-08-20) is
   implemented in RLS and in the API: access requires `consultant_clients.status = 'active'`
   (`supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql`;
   `backend/api/consultant_auth.py::ensure_consultant_org_access`). D19/D27 add
   `suspended/ended` lifecycle columns and the `/end` transition
   (`supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql`;
   `backend/api/v3_consultants.py:716`). WS6/SEC-0003 fixes **who** may revoke
   (`supabase/migrations/20260831040000_consultant_revocation_roles.sql`). D15 also states the
   termination *"is **not** a claim of ownership over the client or its data"*.
4. **The report-artefact storage model is fully ratified** (`B4-D5/D6/D7`): bucket
   `report-artifacts` (schema-`CHECK`-enforced), key derived by `CHECK` as
   `{organization_id}/{report_id}/{version_id}.pdf`, `UNIQUE (report_version_id)`, SHA-256
   lowercase hex, append-only (no `UPDATE`/`DELETE` grant or policy), organisation-scoped read for
   org members and insert for org Owner/Admin. **No consultant id appears anywhere in artefact
   identity.** (`supabase/migrations/20260919000000_p8_b4_frozen_artefact.sql`.)
5. **Storage entitlement is organisation-level**, supplied by the organisation's plan
   (`billing_plans.included_storage_bytes`), measured per organisation per month
   (`usage_tracking.total_storage_bytes`, `UNIQUE (organization_id, usage_month)`), with
   versioned platform commercial rules (`billing_commercial_config` key `storage`), surfaced by
   `backend/services/billing.py::get_entitlement(organization_id)`.
6. **Retention is purpose-based, configurable, server-side, soft-delete only and never invented**
   (frozen decision **N3**; `docs/architecture/CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md`;
   `backend/services/retention.py`). Reports, evidence, snapshots, emissions logs and the audit
   ledger are `INDEFINITE` by design (`B4-D8`).
7. **Signed URLs, not public URLs, are the decided document access mechanism** (D32,
   `supabase/migrations/20260823000000_d32_private_documents_storage.sql`;
   `backend/services/storage.py`), and **authorization precedes signing** at every traced V3 call
   site.
8. **There is no `customer/` and no `consultant/` storage namespace anywhere in the repository.**
   A repository-wide search for the provisional patterns (`consultant/{…}`, `client/{…}`,
   `customer/{…}`) returns **zero** matches in code, migrations, SQL or documentation. The only
   physical namespace in use is the org-scoped `uploads/<organization_id>/…` prefix, which is
   **shared by customer and consultant uploads alike** through the single function
   `backend/api/v3_documents.py::create_document_and_enqueue` (its own docstring: *"Used by the
   org-member upload AND the consultant client upload"*).

### 1.2 What remains genuinely undecided (cannot be answered from existing evidence)

Only these are carried to §8: (a) whether a consultant-originated upload must be **physically
distinguishable** from a customer-originated one; (b) the shape of any such key; (c) whether
multi-firm service of one client is *desired and to be enforced* (exclusivity / handover) or merely
permitted by the schema; (d) the **object-level disposition** on grant revocation and on
organisation offboarding; (e) duplicate-upload identity (content hash / dedupe) for documents;
(f) whether storage entitlement gains a consultant-firm dimension, and which of two contradictory
legacy limits is authoritative; (g) whether direct storage (user-JWT) access should ever extend to
consultants; (h) the upload-audit and download/access-audit requirement for documents.

### 1.3 One asymmetry the PO should see before choosing a key model

The consultant API can **list** and **upload** a client's documents
(`GET|POST /api/v3/consultants/clients/{client_id}/documents`) but exposes **no** signed-URL or
content route, and the storage-layer policies (`d32_documents_*`) contain **no consultant branch**
— they authorise `organization_members` only. Consultant access to document **content** is
therefore not established by the current implementation, while the application-layer tenancy model
(`is_org_consultant` on `organization_files`) *does* permit consultants to read the document
**rows**. A key model that encodes the consultant firm would be encoding an authorization axis that
the storage layer does not currently honour (§6.2; §7 F-2).

---

## 2. Evidence Hierarchy

Sources were weighted in this order. Where two tiers disagree, the higher tier was **not** used to
silently overrule the lower one — the disagreement is recorded in §7 (governance rule 13).

| Tier | Class | Sources used here | Why authoritative |
|---|---|---|---|
| **T1** | Ratified PO decisions and frozen decisions | `D2` §§6/12–25/36 (via the P17 decision contract), `D1` §§2/4/9/11, `D7`/`D7c` (`PO-PHASE6-D7-R-20260910`), `D15`, `D19`, `D20`, `D27`, `D32`, `D33`, `D37-0`, `B2-D2`, `B4-D5/D6/D7/D8`, `CT-FINAL-01`, `N3`, `PX-7`, `FIN-06`, `WS6/SEC-0003`, `P8-D17-D32-STORAGE-POLICY-RESOLUTION-001` (Route C), `D-11` | These are decisions the PO has already taken; rule 14 forbids asking the PO to re-decide them. |
| **T2** | Applied database reality (catalogue probe) | `ENV-LOCAL` and `ENV-LIVE` `pg_indexes`, `pg_policies`, `pg_constraint`, `information_schema.columns`, `storage.buckets`, `storage.objects` | Executable truth. A constraint or policy present in the catalogue is `IMPLEMENTED BEHAVIOUR` regardless of what any document says. |
| **T3** | Migration chain (DDL as code, applied or pending) | `supabase/migrations/00000000000000_init_schema.sql`, `20260803000000_rc2_rls`, `20260821000000_d20_d15_active_consultant_grant`, `20260823000000_d32_private_documents_storage`, `20260824020000_d37_0_billing_security_and_configurable_subscription`, `20260831040000_consultant_revocation_roles`, `20260910120000_p6_2d_consultant_provenance`, `20260919000000_p8_b4_frozen_artefact`, `20260924000000_p8x_x2_operational_telemetry_retention`, `20260927000000_p8_fin06_manual_processing_governance`, `20261010000000_p17a_accounting_dimensions_and_factor_governance`, `20261024000000_ct_final_01_documents_bucket_size_limit`, plus `database/rc1|rc2/*.sql` | Declares intended schema and states the decision it implements. A migration that is **not applied** is `DOCUMENTED INTENT`, not current behaviour. |
| **T4** | Application code (traced) | `backend/api/v3_documents.py`, `backend/api/v3_consultants.py`, `backend/api/consultant_auth.py`, `backend/api/dependencies.py`, `backend/data/organization_files.py`, `backend/data/consultants.py`, `backend/services/storage.py`, `backend/services/retention.py`, `backend/services/billing.py`, `backend/routes/upload.py`, `backend/routes/organizations/files.py`, `backend/routes/admin/dashboard.py`, `backend/utils/upload_limits.py` | The actual shipped behaviour (`CODE-TRACED`). |
| **T5** | Tests | `test_storage_security.py`, `test_ct_final_01_upload_limits.py`, `test_document_content_type.py`, `test_legacy_upload_idor.py`, `test_consultant_revocation_migration.py`, `test_d19_lifecycle.py`, `test_p6_1b_membership_workspace_authorization.py`, `test_p6_2a_consultant_processing_authorization.py`, `test_v3_consultants.py`, `test_scope_aware_authorization.py`, `test_v3_rls_behavior.py` | Evidence of asserted intent and of what is *guarded*; not authority for what the product should do. |
| **T6** | Architecture / design documents | `CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §37, `CarbonTally_V3_Architecture_Specification_v1.0.md`, `CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md`, `CT-PO-P17-ARCH-01`, `CT-PO-P17-ARCH-02`, `CT-PO-P17-POST-ARCH-DECISIONS`, `CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION`, `CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md`, `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` | `DOCUMENTED INTENT`. Supporting evidence only; several predate the migrations that superseded them (see §7). |
| **T7** | Third-party / historical audit reports | `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/research/carbontally_dim02_rules_search_reporting.md`, `docs/ohd/reports/CT-P8-CURRENT-STATE-GAP-RECONCILIATION-AND-CONSULTANT-CLIENT-PARITY-20260915.md`, `docs/cline/reports/P8-FINALIZATION-*` | **Evidence and recommendations only — never authoritative.** Where a T7 report contradicts T2/T3 the contradiction is recorded in §7 (this happened for finding A6 — §7 C-1). |
| **T8** | The Storage Management baseline | `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md` | Used strictly as an **evidence index** (governance rule 15). Every claim re-used from it was re-verified against T1–T4 and is cited at the underlying source. |

Terminology preserved verbatim from the repository: *organisation*, *consultant firm /
`consultant_profiles`*, *consultant member (`consultant_firm_members`)*, *client grant
(`consultant_clients`)*, *client organisation*, *Processing Entity*, *internal staff*, *frozen
artefact*, *object key*, *documents bucket*, *`report-artifacts`*, *signed URL*, *retention*,
*acting-for*.

---

## 3. Decision-by-Decision Evidence Matrix

### 3.1 Master matrix (Q1–Q10)

| Question | Existing answer | Status | Evidence | Conflicts/Gaps |
|---|---|---|---|---|
| **Q1** Can one client organisation have multiple consultant firms? | **YES.** Uniqueness is on the *pair* `(consultant_id, organization_id)`; nothing constrains `organization_id` alone. The system is designed around the possibility (two-firm notification path; lifecycle branch "client chooses another consultant"), but exclusivity/handover is not enforced and has no API/UI flow. | **ESTABLISHED (YES)** — with `PARTIAL` enforcement | T2: `pg_indexes` both envs → `consultant_clients_consultant_id_organization_id_key UNIQUE (consultant_id, organization_id)`. T3: `00000000000000_init_schema.sql` `UNIQUE (consultant_id, organization_id)`; `database/rc1/002_rc1_constraints.sql:311`. T6: actor model §37.3; §37.4(c); P6-2F IV report IV-N2. T4: `data/consultants.py::list_clients/get_client_by_org` are per-*firm* lookups; `is_org_consultant` matches `cc.consultant_id = cfm.firm_id`. | §7 C-1 (Kimi A6 asserts the opposite). No exclusivity constraint; no handover workflow; no UI/API flow (§37.3, §37.4). |
| **Q2** Ownership model for consultant-uploaded documents | **The client organisation owns it.** The consultant firm is never the data owner; the consultant *member* is uploader/provenance only. | **ESTABLISHED** (`EXISTING DECISION`) | T1/T6: P17 decision contract rows 9–11 (D2 §§6/22/24/25); `CT-PO-P17-ARCH-01` §57.1 row 7; `CarbonTally_V3_Architecture_Specification_v1.0.md` "Customer / Organization — the customer tenant (data owner)". T3: `organization_files.organization_id → organizations(id)` is the only tenancy key. T6: actor model §37.5 "`consultant_clients` … never the data owner". T4: consultant upload docstring — *"the document is stored under the client organisation's private bucket path"*. | The **firm** is not recorded on the document at all (no firm column on `organization_files`) → provenance gap §7 C-6. |
| **Q3** What happens when a grant is revoked? | **Access revocation only** — immediately and uniformly, in RLS and API; the relationship row is retained as provenance, and **no data is deleted, moved, archived or reassigned by any traced code path**. Object-level disposition is not specified. | **Access: CLOSED/IMPLEMENTED. Object lifecycle: NOT ESTABLISHED** | T1: D15 (approved 2026-08-20). T3: `20260821000000_d20_d15_active_consultant_grant.sql` (`status='active'` required); `20260822010000_d27_d19_customer_lifecycle.sql` (suspended/ended/ended_by); `20260831040000_consultant_revocation_roles.sql` (who may revoke). T4: `consultant_auth.py::ensure_consultant_org_access`; `v3_consultants.py::end_client` (716). T5: `test_d19_lifecycle.py::test_ended_grant_loses_client_access`; `test_p6_1b…::test_revoked_membership_denied_on_fresh_evaluation`. T6: §37.5 "Data preservation" table. | No documented or implemented rule for object deletion/movement/archival/reassignment on revocation → §8 PO decision 4. |
| **Q4** Are customer vs consultant uploads physically distinguished? | **No.** Both ingress paths call one function that writes `uploads/{organization_id}/{YYYY/MM/DD}/{uuid4().hex}_{filename}` — identical shape, identical prefix, same bucket. | **Customer/consultant distinction: NOT ESTABLISHED. Current unified namespace: IMPLEMENTED.** | T4: `api/v3_documents.py::create_document_and_enqueue` (path construction + docstring); `api/v3_consultants.py::upload_client_document` (calls it). T3: D32 policy predicate requires `foldername[1]='uploads' AND foldername[2]::uuid ∈ organization_members` — no consultant segment. | No `customer/…` or `consultant/…` string exists anywhere in the repo (`grep` → 0 matches). §5, §7 C-4/C-5. |
| **Q5** Can consultants access customer-uploaded documents? | **Conditionally:** the consultant surface can list/upload a client's documents and the tenancy RLS grants consultants `SELECT` on the document **rows**, but no consultant route returns document **content/signed URL**, and the storage-layer policies exclude consultants entirely. | **PARTIAL / CONFLICTING between layers** | T3: `20260803000000_rc2_rls.sql` §3 tenant loop (`_tenant_select … is_org_member OR is_org_consultant`); `organization_files_tenant_select` present in both envs (T2). T4: `v3_consultants.py` route inventory (list/upload only, **no** `signed_url`); `v3_documents.py::{get_document,get_document_signed_url}` require `require_org_member()`; `services/storage.py` docstring. T2: `d32_documents_select_org_member` predicate references `organization_members` only. | Layer asymmetry §6.2; §7 C-3. Whether consultants *should* see content is **not established** → §8 PO decision 9. |
| **Q6** Can customers access consultant-uploaded documents? | **Yes — they are indistinguishable from customer uploads.** Same table, same `organization_id`, same client-facing surface; `uploaded_by` merely records the consultant's user id. | **IMPLEMENTED (by construction); DOCUMENTED INTENT in code; no separate ratified statement** | T4: `api/v3_consultants.py::upload_client_document` docstring (*stored under the client organisation's private bucket path … SAME durable pipeline as a customer upload*); `v3_documents.py` list/`signed-url` require only org membership. T3/T2: client members satisfy `organization_files_tenant_select` and `d32_documents_select_org_member`. | No ratified PO text says *"customers may read consultant-uploaded documents"* as a separate rule; it follows from the ownership + tenancy model (Q2). Consistency is a consequence, not an explicit decision. |
| **Q7** Is duplicate upload identity defined? | **No.** There is no content hash, checksum, or dedupe identity on documents or objects; identity is a fresh `uuid4` per upload plus an `organization_files` row per upload. The same physical bytes uploaded twice become **two objects and two rows**. | **NOT ESTABLISHED** | T2 `ENV-LOCAL`: `organization_files` constraints are only `pkey(id)`, `organization_files_organization_id_fkey`, `organization_files_size_bytes_check`; its 26 columns contain no checksum/hash column. T3 `00000000000000_init_schema.sql:541-568`. T4: `create_document_and_enqueue` uses `uuid4().hex` in the key and `repos.files.create(...)` unconditionally; no pre-insert lookup exists. | A **recommendation** to add `file_checksum` appears in a third-party audit (`Final_Kimi` dim02 finding **A5**) — that is T7 evidence, **not** a CarbonTally decision. See §7 C-2 and §8 PO decision 5. |
| **Q8** Established report-artefact storage model | **Bucket** `report-artifacts` (private, `CHECK`-forced); **key** `{organization_id}/{report_id}/{report_version_id}.pdf` (derived by `CHECK`); **one row per finalised version** (`UNIQUE (report_version_id)`); **SHA-256** lowercase hex; **append-only**; **organisation-scoped** RLS (`p8_disclosure_is_org_member` read / `p8_disclosure_is_org_admin` insert); **no consultant id in artefact identity**. | **CLOSED — ratified `B4-D5/D6/D7`** (provisioning `MISSING`) | T3: `20260919000000_p8_b4_frozen_artefact.sql` (bucket CHECK line 67, key CHECK lines 70-72, sha256 CHECK 73-74, `UNIQUE` line 65, RLS 103-115). T6: `REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` (key + TTL 300 s); `CarbonTally_V3_Architecture_Specification` / D2 §24 (belongs to the client org). T2: `storage.buckets` in **both** envs contains only `documents` → `report-artifacts` absent (`MISSING`). | The bucket is mandated by schema `CHECK` but does not exist in either probed environment; `D-11` decided *operational* provisioning (no migration, no `create_bucket`). Execution gap, not a decision gap — §7 C-7. |
| **Q9** Which entity owns storage quota? | **The organisation.** Entitlement = org's plan `included_storage_bytes`; usage = org-scoped monthly `usage_tracking.total_storage_bytes`; platform commercial defaults = versioned `billing_commercial_config['storage']`; consumed by `get_entitlement(organization_id)`. Consultant-firm-level storage quota is **not established**. | **Organisation-level: CLOSED/IMPLEMENTED. Consultant-level: NOT ESTABLISHED** | T3: `20260824020000_d37_0_…` (`billing_plans.included_storage_bytes` line 126; `billing_commercial_config` keys incl. `storage` line 179 and seed lines 269-275); `00000000000000_init_schema.sql:1480-1493` (`usage_tracking`, `UNIQUE (organization_id, usage_month)`). T4: `services/billing.py::get_entitlement` returns `"storage": {usage_bytes, included_bytes, additional_bytes}` and `config_versions.storage`; `api/v3_billing.py:102`. | Two contradictory legacy hard-coded limits (`routes/organizations/files.py:764` 5 000 MB; `routes/admin/dashboard.py:699` 50 GB "(example)") vs plan-based entitlement → §7 C-8; §8 PO decision 6. `consultant_billing` (init schema:1618) has extraction-credit columns and **no** storage column, and is not referenced by any non-test Python module. |
| **Q10** Deletion / retention / audit / signed URLs | Mixed — see the classification table in §3.3. | **PARTIAL overall** | T1/T3/T4/T6 as itemised in §3.3 | §3.3 lists the exact conflicts; §8 carries the genuinely undecided items. |

### 3.2 Q10 — classification (Deletion)

| Sub-question | Existing state | Class | Evidence |
|---|---|---|---|
| **Soft delete of a document** | Implemented twice: `organization_files.deleted_at` (retention) and `is_active = FALSE` (`OrganizationFilesRepository.delete`); the legacy route also sets both (`is_active=False` + `deleted_at`). | **IMPLEMENTED** | `backend/data/organization_files.py:25-29, 154-157`; `backend/routes/organizations/files.py` `DELETE /{file_id}` (soft branch). Column confirmed live (`ENV-LOCAL`: `deleted_at`, `is_active`). |
| **Permanent delete of a document** | Only in the **legacy** router (`DELETE /api/organizations/files/{file_id}?permanent=true`, `require_org_member()`): it attempts the storage `remove()` inside `try/except` that **swallows storage errors and continues**, then deletes the `organization_files` row unconditionally — i.e. the row can be lost while the object remains (orphan). No V3 equivalent exists (`grep -i delete backend/api/v3_documents.py` → no route). | **PARTIAL / CONFLICTING** | `backend/routes/organizations/files.py:437-475` (`print("⚠️ Storage deletion error: …")` then `.delete()`); `backend/main.py:255` mounts the router (`prefix="/api/organizations/files"`). |
| **Object deletion (storage-first, verified)** | No code path removes an object **and** verifies removal before retiring metadata; no object-lifecycle service exists. | **NOT ESTABLISHED** | `grep 'storage.from_('` across `backend/api|services|data|routes` → only `upload`, `download`, `create_signed_url`, `remove` (legacy), plus the artefact adapter. |
| **Orphan handling** | No sweeper, reconciler, or orphan-detection job exists for storage objects or document rows. "Orphan" appears in the codebase only for unrelated domains (validation factor orphans, adjudication rows). | **NOT ESTABLISHED** | repo-wide `grep -i orphan` → `backend/data/emissions_logs.py:266`, `activity_clarifications.py:296`, `engines/validation.py` — none storage-related. |
| **Deletion audit** | No audit entry is written when a document/object is deleted by any path. | **NOT ESTABLISHED** | No `repos.audit.record` call in `organization_files.py`, `v3_documents.py` delete paths (there are none), or the legacy delete handler. |

### 3.3 Q10 — classification (Retention)

| Sub-question | Existing state | Class | Evidence |
|---|---|---|---|
| **Retention governance (who decides, how enforced)** | Decided and frozen: retention is **configurable, admin-only, server-side, purpose-based, never invented, soft-delete only, dry-run by default**. Values live in `system_settings`; exposed at `/api/v3/settings/retention`; enforced by `backend/services/retention.py`. | **CLOSED** | T1 `N3`; `docs/architecture/CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md` §1–§5; `backend/services/retention.py` module docstring; `supabase/migrations/00000000000000_init_schema.sql:2077-2079, 2080+` (`audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`). |
| **Document retention** | `document_retention_days` is one of exactly **two** enforced domains (`_ELIGIBLE_DOMAINS`); enforcement calls `repos.files.expire_documents_older_than(cutoff, dry_run=…)`, which **only** sets `deleted_at`. | **PARTIAL (implemented; value unset)** | `services/retention.py:36, 98-110`; `data/organization_files.py:150-177`. The setting ships **NULL** ("not configured") → nothing is purged today. |
| **Object retention (`storage.objects`)** | The CT-FINAL-01 matrix lists *"Uploaded source documents (`organization_files` + `storage.objects`)"* as one CONFIGURABLE domain, but the enforcement path touches **only** the row — the storage object is never deleted by retention. | **CONFLICTING** | `CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md` §2 row 2 vs `retention.py:98-110` + `expire_documents_older_than`. See §7 C-3. |
| **Report / artefact retention** | Reports, versions and frozen artefacts are **INDEFINITE by design**; the B4 migration states *"No retention artefact (B4-D8 is still an open PO decision)"* — i.e. B4-D8 itself is the open decision, and the operative rule is *exclude from all retention*. | **CLOSED as "indefinite"; the artefact-retention *policy* value remains a PO decision** | `20260919000000_p8_b4_frozen_artefact.sql` header lines 24-27; `retention.py:41-50` `_TELEMETRY_EXCLUDED_TABLES` includes `report_versions`, `report_version_artifacts`; `CT-FINAL-01-…` §2 row 8 (`INDEFINITE`, `B4-D8`). |
| **Evidence / snapshot / emissions / audit retention** | Explicitly outside every retention rule; audit is append-only at the database. | **CLOSED** | `retention.py:41-50`; `CT-FINAL-01-…` §2 rows 3-7; `20260924000000_p8x_x2_…` header lines 63-68 ("reports, evidence, audit — untouched (B4-D8 retention remains indefinite)"). |
| **Operational telemetry retention** | `operational_telemetry_retention_days` default **90**, configurable, scoped to alert/metrics stores only. | **CLOSED/IMPLEMENTED** | `20260924000000_p8x_x2_operational_telemetry_retention.sql`; `retention.py:112-147`. |
| **Organisation offboarding retention** | No offboarding retention or export/erasure workflow exists; the actor model records it as an `ARCHITECTURAL GAP / NOT SUPPORTED` and the P8 finalisation report states *"Retention period / retirement remains product work (report §Q.3)"*. | **NOT ESTABLISHED** | actor model §37.5–§37.6; `docs/cline/reports/P8-FINALIZATION-IMPLEMENT-001.md` (destructive-change row: *"Deferred decision — Retention period / retirement remains product work"*). |

### 3.4 Q10 — classification (Audit and Signed URLs)

| Sub-question | Existing state | Class | Evidence |
|---|---|---|---|
| **Upload audit** | No audit entry is written by any upload ingress. The V3 ingestion pipeline records `created_by`/`uploaded_by` and an enqueue-outcome digest in `organization_files.metadata`, but writes **no** `audit_logs` / `audit_trail` row. | **NOT ESTABLISHED** (partially substituted by metadata) | `api/v3_documents.py::create_document_and_enqueue` (metadata accumulator only); `grep -n audit backend/api/v3_documents.py` → the only audit write is the D33.1 evidence drill-down (line 635-657). `OrganizationFilesRepository` writes no audit. |
| **Download / access audit** | One narrow, ratified case exists: **D33.1** append-only evidence-access audit on `GET /api/v3/documents/{file_id}/emissions` (`entity_type='organization_files'`, `action='evidence.reverse_lookup'`, ids only, never URLs or secrets). No audit is written for `GET /documents/{id}/signed-url`, `GET /documents/{id}`, or the consultant document list. | **PARTIAL** | `api/v3_documents.py:632-680` (D33.1); **no** equivalent in `get_document` / `get_document_signed_url` (lines 580-616); `api/v3_consultants.py` has no audit write on `client_documents`. |
| **`access_count` / `last_accessed` telemetry** | Columns exist on `organization_files` but are **never updated** by any non-test module (they are only ever selected, or initialised to `0` by the legacy writer). | **NOT ESTABLISHED (dead telemetry)** | `ENV-LOCAL` `information_schema.columns` (`access_count`, `last_accessed` present); `data/organization_files.py:15, 58` (select only); `routes/upload.py:740` (`'access_count': 0` on insert); no `SET access_count` / `SET last_accessed` anywhere in `backend/`. |
| **Signed-URL generation audit** | Issuing a signed URL is not itself audited (neither the document nor the ETTL/expiry is recorded). | **NOT ESTABLISHED** | no audit call adjacent to any `storage_signed_url` call site (`v3_documents.py:314, 611`; `v3_emissions.py:463`; `v3_evidence.py:158`). |
| **Retention audit** | `enforce_retention()` returns a structured dry-run/applied **report** to its caller; it writes no audit row and no retention-run record exists. | **PARTIAL** | `services/retention.py::enforce_retention` return value; no `repos.audit.record` in the module. |
| **Deletion audit** | See §3.2 — none. | **NOT ESTABLISHED** | — |
| **Authorization before signing** | Implemented at every traced V3 site: the caller is authorised (`require_org_member()` + `ensure_org_access(…, doc.organization_id)`) **before** `storage_signed_url()` is called; the helper is documented as *"Authorization is enforced by the API layer … BEFORE any signed URL is issued"*. | **IMPLEMENTED** | `api/v3_documents.py:594-616`; `api/v3_emissions.py:405-463` (`ensure_org_access` before signing); `api/v3_evidence.py:154-192`; `services/storage.py` docstring + `storage_signed_url`; `routes/organizations/files.py:390-425` (legacy, `require_org_member()` + `.eq('organization_id', org_id)`); tests `test_storage_security.py::test_signed_url_org_member_allowed|cross_org_denied|unknown_document_404`. |
| **URL lifetime** | Mandatory and explicit: documents **3 600 s** (`SIGNED_URL_TTL_SECONDS`, returned as `expires_in_seconds: 3600`); the helper documents "*expiry is mandatory — signed URLs always expire*". The frozen artefact uses **300 s** with an authorisation-gated endpoint (`v3_disclosure.py::get_frozen_artefact_signed_url`). | **IMPLEMENTED** | `services/storage.py:30, 58-72`; `api/v3_documents.py:611-616`; `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` §1 ("TTL 300 s … issued **after** authorization"). |
| **URL persistence** | **Conflicting.** A signed URL *is* persisted at upload time (`organization_files.metadata.file_url = storage_signed_url(path)`), so a stored row carries an already-expired 1-hour URL; consumers are expected to re-sign from the canonical `path`. `path` (not the URL) is the durable locator. | **CONFLICTING** | `api/v3_documents.py:314, 319` (`file_url = storage_signed_url(path)` → `metadata={"data_type":…, "file_url": file_url}`) vs the same block's comment: *"The canonical PATH is stored on the record; consumers request a fresh signed URL per view."* `services/storage.py::path_from_url` exists precisely because *"legacy rows stored public URLs"*. |
| **Durable object identity** | `organization_files.path` is the canonical bucket-relative locator; identity is the row `id` (UUID) plus `(bucket, path)`. **No content identity / hash** exists (Q7) — so object identity is durable but content identity is not. | **PARTIAL** | `api/v3_documents.py:319`; `services/storage.py::path_from_url`; §3.2/Q7. |

---

## 4. Consultant / Client Relationship Model

### 4.1 The forward chain (implemented)

```text
authenticated user
   │
   │  consultant_firm_members (user_id, firm_id, role, can_* flags, client_access uuid[], is_active)
   ▼
Consultant firm  =  consultant_profiles (id; user_id; is_active; organization_id → organizations,
   │                                  organization_type='CONSULTANT' — added by P17-A, nullable)
   │
   │  client grant = consultant_clients (consultant_id → consultant_profiles.id,
   │                                    organization_id → organizations.id,
   │                                    status, suspended_at, ended_at, ended_by,
   │                                    relationship_origin, engagement lifecycle)
   │                UNIQUE (consultant_id, organization_id)
   ▼
Client organisation = organizations (id, is_active, archived_at, organization_type,
                                     subscription_* / billing_mode, customer_type)
```

Evidence per hop:

| Hop | Constraint / rule | Evidence |
|---|---|---|
| user → member | `consultant_firm_members.firm_id → consultant_profiles(id)`, `user_id → users(id)`, both `ON DELETE CASCADE`; `role` + four `can_*` flags + `client_access uuid[]` + `is_active` | `00000000000000_init_schema.sql` (`consultant_firm_members`); `data/consultants.py::get_active_memberships_by_user`; `api/consultant_auth.py::_resolve_context` |
| member → firm | The caller's active memberships must resolve to **exactly one distinct firm**, else `_resolve_context` returns `None` → **denied** ("ambiguous under the single-firm assumption") | `api/consultant_auth.py:76-118`; test `test_p6_1b_membership_workspace_authorization.py::test_multiple_active_firms_ambiguous_denied` |
| firm → grant | `consultant_clients.consultant_id` FK; grant status vocabulary `active / pending / rejected / suspended / ended / inactive`; **only `active` authorises** | `00000000000000_init_schema.sql` (`consultant_clients`); `20260822010000_d27_d19_customer_lifecycle.sql`; `api/consultant_auth.py:63-65` (`CLIENT_STATUSES`) |
| grant → client org | `consultant_clients.organization_id → organizations(id)` **both FKs `ON DELETE CASCADE`**; the grant row is *"never the data owner"* | actor model §37.2, §37.5; `20260831040000_consultant_revocation_roles.sql:8-13` |

**Important nuance (does not contradict Q1).** The single-firm rule above constrains a
**consultant user**: one person cannot act for two firms. It says nothing about how many **firms**
may hold grants to one **client organisation**. Keeping these two directions apart is essential:

| Direction | Cardinality in the schema / business rule | Status |
|---|---|---|
| One consultant **user** → firms | **Exactly one** active firm (multi-firm ⇒ denied) | `IMPLEMENTED` (`_resolve_context` ambiguity guard) |
| One consultant **firm** → client orgs | **Many** (standard multi-client consultancy) | `IMPLEMENTED` (`consultant_clients` rows; `list_clients`) |
| One **client org** → consultant firms | **Many permitted**; no exclusivity, no uniqueness on `organization_id` | `ESTABLISHED` at schema/permission level; **not enforced; no API/UI/handover** |

### 4.2 The reverse relationship: Customer Organisation → one or multiple Consultant Firms?

**Answer: multiple firms may hold simultaneous grants to one customer organisation.** This is
established by more than a foreign key — by the *absence of an exclusivity constraint* on
`organization_id`, by the firm-keyed authorization predicate, and by documents that reason about
the case directly:

1. **Constraint evidence (T2, `LIVE — READ-ONLY VERIFIED`).** `ENV-LOCAL`:
   `consultant_clients_consultant_id_organization_id_key` **and**
   `consultant_clients_consultant_org_uniq`, both `UNIQUE (consultant_id, organization_id)`;
   `ENV-LIVE`: `consultant_clients_consultant_id_organization_id_key` (same columns). Neither
   environment has any unique index on `organization_id` alone. Live rows: `ENV-LOCAL` 3 rows /
   3 firms / 3 orgs (each org currently has exactly one firm — the *data* does not exercise the
   case; the *schema* permits it); `ENV-LIVE` 0 rows.
2. **RLS evidence — the predicate is deliberately firm-keyed.**
   `is_org_consultant(p_org)` matches `cc.consultant_id = cfm.firm_id AND cc.organization_id = p_org
   AND cc.status = 'active'`. It asks *"does **this caller's firm** have an active grant for this
   org?"* — never *"is this caller the only firm?"* (`20260821000000_d20_d15_active_consultant_grant.sql`;
   `20260803000000_rc2_rls.sql:86-108`). Grant-management RLS is likewise firm-scoped
   (`cc_select_own_firm`, `cc_insert_own_firm`, `cc_update_own_firm`, `cc_delete_own_firm`), so
   **firm Y cannot see or delete firm X's grant** for the same client — a strong signal that
   co-existing grants are an anticipated state.
3. **Documented evidence.**
   * actor model §37.3: *"Multiple consultant grants to one org are schema-representable … 'client chooses another consultant' is data-representable"*;
   * actor model §37.4(c) (approved direction): *"Consultant switch: representable today at the data level (multiple firms may hold grants to one org); requires an explicit handover workflow …"*;
   * P6-2F IV report IV-N2 reasons about *"two firms both hold[ing] active grants for the same organisation"*;
   * P8-FINALIZATION-IMPLEMENT-001 (FIN-06) records the platform scope vocabulary
     `organization | consultant_firm | consultant_client` and states *"'All clients of a firm' = one
     firm row; 'selected clients' = one row per client"* — a firm-keyed control that presumes
     co-existing firm rows (`20260927000000_p8_fin06_manual_processing_governance.sql:67-82`).

**What is *not* established.** That the platform *wants* co-existing firms, that it should
*prevent* them (exclusivity), or how a switch/handover is executed. §37.3 lists these as
`ARCHITECTURAL GAP`; §37.4(c) is an approved *direction* only. → §8 PO decision 3.

**Explicitly NOT evidence for Q1:** the "single active firm" ambiguity guard (§4.1) and the
`test_multiple_active_firms_ambiguous_denied` test — both concern one **user** in several **firms**,
the opposite direction.

### 4.3 Storage consequence of the relationship model

Because the client organisation owns the data and the relationship is a *revocable grant*, storage
identity is currently anchored **only** on the client organisation. Two firms uploading for the
same client therefore produce objects that are indistinguishable in the namespace
(`uploads/<client_org_id>/…`), and the consultant firm's identity exists on the **processing items**
only:

* `public.manual_extraction_items.consultant_firm_id` — ratified **D7** firm-provenance column,
  server-derived at action time, **write-once**, `ON DELETE SET NULL`, no historical backfill
  (`20260910120000_p6_2d_consultant_provenance.sql`; `data/manual_extraction.py:711-725`;
  `api/consultant_auth.py::resolve_consultant_firm_id`).
* **Nothing equivalent exists for the uploaded document/object.** `organization_files` has no
  `consultant_firm_id` / `processing_mode` column (confirmed by `ENV-LOCAL`
  `information_schema.columns`, 26 columns, §9.1). Firm attribution for an upload is therefore
  inferable only from `uploaded_by` (a user id) plus membership history at that time — and
  membership is mutable, which is exactly why the D7 decision forbids deriving provenance from
  current membership. This is a genuine provenance gap (§7 C-6), and it is a design input for the
  PO's key decision (§8 decisions 1–2).

---

## 5. Storage Namespace Evidence

### 5.1 CURRENT — every object-key producer traced in code (`CODE-TRACED`)

| # | Producer (ingress) | Bucket | Object key | Authorisation | Evidence |
|---|---|---|---|---|---|
| P1 | **V3 canonical pipeline** — `POST /api/v3/uploads` (organisation member) **and** `POST /api/v3/consultants/clients/{client_id}/documents` (consultant, `can_upload_documents`) — both call `create_document_and_enqueue()` | `documents` | `uploads/{organization_id}/{YYYY/MM/DD}/{uuid4().hex}_{filename}` | `require_org_member()` + `ensure_org_access` (+ viewer read-only refusal) / `require_consultant()` + `_authorized_client_org` + `can_upload_documents` | `api/v3_documents.py:288`; `api/v3_consultants.py:1274-1320`; `test_ct_final_01_upload_limits.py::test_v3_document_upload_enforces_the_effective_limit_before_storage` |
| P2 | Legacy `POST /api/upload` (mounted at `/api`) | `documents` | `uploads/{organization_id}/{YYYY/MM/DD}/{YYYYMMDD_HHMMSS}_{filename}` | legacy handler; guarded by `test_legacy_upload_idor.py`, `test_ct_final_01_upload_limits.py::test_legacy_upload_route_rejects_a_foreign_organization` | `routes/upload.py:703` |
| P3 | Legacy `POST /api/organizations/files/upload` (+ bulk at line 865) | `documents` (or row `bucket`) | `organizations/{org_id}/{YYYY/MM}/{clean_name}_{YYYYMMDD_HHMMSS}.{ext}` | `require_org_member()` + explicit `str(org_id) != str(current_user.organization_id)` → 403 | `routes/organizations/files.py:115-129, 580, 865` |
| P4 | Legacy `POST /api/repair-pdf` | `documents` | `repaired_pdfs/{repaired_YYYYMMDD_HHMMSS_filename}` | legacy handler | `routes/upload.py:486` |
| P5 | **Frozen report artefact** (internal generation, not an upload ingress) | `report-artifacts` | `{organization_id}/{report_id}/{report_version_id}.pdf` (schema-derived) | `v3_disclosure.py::get_frozen_artefact_signed_url`, 300 s TTL | `domain/report_artefact.py`; `20260919000000_p8_b4_frozen_artefact.sql:70-72` |
| P6 | **No traced producer** — present in live storage only | `documents` | `batches/<org_id>/…`, `manual_review/<org_id or literal>/…` | none | `ENV-LIVE` `storage.objects` aggregate: `manual_review/*` = 38, `uploads/*` = 14, `batches/*` = 6 (58 total) |

**Findings from the key model.**

* **The customer/consultant distinction does not exist in the key.** P1 is one function; its own
  docstring says *"Used by the org-member upload AND the consultant client upload"*. There is no
  marker, segment, suffix or bucket difference between a customer-originated and a
  consultant-originated object.
* **The namespace is far from uniform.** Six producers, five first-segment prefixes
  (`uploads/`, `organizations/`, `repaired_pdfs/`, `batches/`, `manual_review/`), two second-segment
  semantics (`<uuid>` and `<literal>`), plus the artefact bucket's own layout.
* **Storage RLS covers one prefix only.** The D32 predicate requires
  `foldername(name)[1] = 'uploads' AND foldername(name)[2]::uuid IN (select organization_id from
  organization_members where user_id = auth.uid() and is_active)`. `ENV-LIVE`: **44 of 58 objects
  (76 %)** sit under `manual_review/` or `batches/`, i.e. outside the authorised prefix; and
  `manual_review/unknown`, `manual_review/mock-org-id` would raise a `uuid` cast error rather than
  simply not matching (consequence `UNVERIFIED` — no non-UUID path was exercised). Because all
  application I/O uses the service-role client, this does not block the app's own paths; it means
  the **direct user-JWT path authorises only a subset of the objects that exist**.

### 5.2 TARGET ALREADY DECIDED

| Item | Decision | Status |
|---|---|---|
| Bucket for customer documents | `documents` — **private** (sole bucket in both envs, `public = f`) | `CLOSED` — D32 (`20260823000000_d32_private_documents_storage.sql`: `UPDATE storage.buckets SET public = FALSE WHERE name = 'documents'`) |
| Bucket for frozen artefacts | `report-artifacts`, private, `CHECK`-forced, **no consultant id in the key** | `CLOSED` — `B4-D5/D6/D7` (`20260919000000_p8_b4_frozen_artefact.sql`) |
| Access method | **Short-lived signed URLs only**, never public URLs; authorisation precedes signing | `CLOSED` — D32 + `services/storage.py` + `REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` |
| Upload caps (application) | 10 MB / 50 files / 500 MB aggregate, configurable downward; defaults 6 / 50 / 500 | `CLOSED` — `CT-FINAL-01` (`backend/utils/upload_limits.py`; `test_ct_final_01_upload_limits.py::test_ratified_platform_caps_are_the_documented_ceilings`) |
| Upload cap (storage layer) | `documents.file_size_limit` tightened to the ratified 10 MB | **DECIDED but NOT APPLIED** — `20261024000000_ct_final_01_documents_bucket_size_limit.sql`; `ENV-LIVE` currently **2 097 152 (2 MiB)** |
| Object-path *convention* for documents | `uploads/<org_id>/<date>/<file>` | `DOCUMENTED INTENT` — stated by the D32 migration header/comments and by the demo-lab document; **not** a normalised namespace decision with a normative document |
| Tenant anchor | `organization_id` for every org-scoped record and both buckets' keys | `CLOSED` — actor model §37.2 "Data tenancy spine"; P17 §57.1 row 7 |

### 5.3 PROPOSED / UNDECIDED

| Item | Status | Evidence |
|---|---|---|
| `consultant/{CONSULTANT_ID}/client/{CLIENT_ID}/…` | **NOT ESTABLISHED anywhere.** Repository-wide search for `consultant/{`, `client/{CLIENT`, `customer/{CLIENT` across `*.py`, `*.sql`, `*.ts`, `*.tsx`, `*.md` returns **0 matches**. It exists only as the PO's provisional input to this review. | `grep -rn` as described → no results |
| `customer/{CLIENT_ID}/…` | **NOT ESTABLISHED anywhere** (same search). | as above |
| Whether any such segment *should* exist | **NOT ESTABLISHED.** No document distinguishes customer- from consultant-originated uploads physically; the only decided "who" in a key is the client organisation. | actor model §37.2/§37.5 (everything org-scoped); D2 §24 (data belongs to the client org) |
| Whether the firm id belongs in **any** key | **NOT ESTABLISHED for storage.** For *processing provenance* a ratified decision exists (**D7**: `consultant_firm_id` on `manual_extraction_items`, server-derived, write-once, no backfill) — a precedent the PO may consult, but it is **not** a storage-namespace decision and does not transfer automatically. | `20260910120000_p6_2d_consultant_provenance.sql`; §4.3 |
| Whether a separate bucket per origin is wanted | **NOT ESTABLISHED.** Only two buckets are named anywhere in code/schema (`documents`, `report-artifacts`); no document proposes a consultant bucket. | `services/storage.py::DOCUMENTS_BUCKET`; `domain/report_artefact.py::ARTEFACT_BUCKET`; `ENV-LIVE`/`ENV-LOCAL` `storage.buckets` |

---

## 6. Authorization Evidence

Three independent authorization layers control storage-adjacent access. They are **not** the same
model, and a decision taken in one layer does not automatically hold in another.

### 6.1 Layer 1 — Application (FastAPI dependencies)

| Control | Mechanism | Evidence |
|---|---|---|
| Authentication | Supabase JWT → `AuthUser` | `backend/auth.py::get_current_user` |
| Customer (organisation member) | `require_org_member()`; then `ensure_org_access(current_user, organization_id)` — internal staff bypass, Processing Entity staff always denied, else membership must match the bound organisation | `api/dependencies.py:163-193`; `api/v3_documents.py` (all document routes) |
| Viewer read-only | `POST /api/v3/uploads` refuses `org_viewer` **before** creating any object or row (`CL-42`). **Only that one ingress is guarded** — the legacy `/api/upload`, `/api/organizations/files/upload`, `/api/repair-pdf`, bulk upload and **the consultant upload route** do not perform a viewer check. | `api/v3_documents.py:212-231`; contrast `api/v3_consultants.py:1274+`; legacy handlers |
| Consultant | `require_consultant()` → `_resolve_context()` (active membership, **exactly one** active firm, active firm profile) → then per organisation: `ensure_consultant_org_access()` (active grant) → then per action: `ensure_consultant_permission(context, "<perm>")` using the real `can_*` columns | `api/consultant_auth.py:76-118, 215-239`; `api/consultant_auth.py:44-57` (`CONSULTANT_PERMISSIONS`) |
| Consultant → client resource | `_authorized_client_org(client_id)` = `_checked_client(...)` (firm-ownership; cross-firm → 404) **and** `ensure_consultant_org_access(...)` (inactive/ended grant → 403) | `api/v3_consultants.py:1141-1157` |
| Consultant upload | `_authorized_client_org` **and** `ensure_consultant_permission(context, "upload_documents")` — both before any storage write | `api/v3_consultants.py:1286-1296` |
| Cross-consultant isolation | Every consultant repository lookup is firm-keyed (`consultant_id = <caller's firm>`), and grant RLS is firm-scoped | `data/consultants.py::list_clients`, `get_client_by_org`; `20260803000000_rc2_rls.sql:323-365` |
| Revocation | `POST /clients/{id}/suspend|end|reactivate`, `DELETE /clients/{id}` — state transitions via `transition_client_lifecycle`; granting/ending requires `can_manage_clients`; **who may revoke at the RLS level**: consultant owner/admin/manager (`is_consultant_firm_revoker`) or customer owner/admin (`is_org_admin_or_owner`) | `api/v3_consultants.py:689-743, 879`; `data/consultants.py:389-440`; `20260831040000_consultant_revocation_roles.sql`; tests `test_d19_lifecycle.py`, `test_consultant_revocation_migration.py`, `test_scope_aware_authorization.py::test_e_/test_f_/test_g_` |

### 6.2 Layer 2 — Database RLS (PostgREST / user JWT)

| Table class | Policy | Effect |
|---|---|---|
| All org-scoped tables with `organization_id` (includes `organization_files`, `customer_documents`, `upload_batches`, `manual_extraction_batches`/`items`, `report_*`, `audit_logs`) | `<t>_tenant_select FOR SELECT TO authenticated USING (is_org_member(organization_id) **OR is_org_consultant(organization_id)**)`; INSERT/UPDATE/DELETE are **member-only** | **A consultant may read client-scoped rows but may not write them through the browser client.** `LIVE — READ-ONLY VERIFIED`: all four `organization_files_*` and `customer_documents_*` policies exist in both envs; the consultant branch is in the SELECT policy only. |
| `is_org_consultant(org)` | `EXISTS (cfm WHERE cfm.user_id = auth.uid() AND cfm.is_active AND EXISTS (cc WHERE cc.consultant_id = cfm.firm_id AND cc.organization_id = org AND cc.status = 'active'))` | Firm-keyed, **status-gated**, and **does not consult `client_access`** any more (`client_access` is a per-member shortcut that no longer grants organisation access). |
| `organizations` | `organizations_org_select … is_org_member(id) OR is_org_consultant(id)` | Client org profile readable by its consultants. |
| Grant table | `cc_*_own_firm` (firm-scoped read/insert/update + revoker-scoped delete) and `consultant_clients_tenant_delete` (customer owner/admin) | Firm Y cannot see or delete firm X's grant for the same client. |

Sources: `supabase/migrations/20260803000000_rc2_rls.sql:60-105, 189, 323-365`;
`20260821000000_d20_d15_active_consultant_grant.sql`;
`20260831040000_consultant_revocation_roles.sql`; `database/rc1/004_rc1_rls.sql:120-175`;
`backend/tests/integration/test_v3_rls_behavior.py`.

### 6.3 Layer 3 — Supabase Storage RLS (`storage.objects`, direct user JWT)

The four approved D32 policies are the **only** storage-layer authorisation in existence. Their
predicate (re-read from the catalogue, `LIVE — READ-ONLY VERIFIED`):

```sql
bucket_id = 'documents'
AND (storage.foldername(name))[1] = 'uploads'
AND ((storage.foldername(name))[2])::uuid IN (
      SELECT organization_id FROM public.organization_members
       WHERE user_id = auth.uid() AND is_active = true)
```

| Attribute | Value | Evidence |
|---|---|---|
| Policies | exactly four: `d32_documents_{select,insert,update,delete}_org_member`, `TO authenticated` | `pg_policies` both envs; the migration validates exactly this set and fails closed on drift |
| `anon` / `public` | **never** granted (the migration raises if any policy broadens) | `20260823000000_d32_private_documents_storage.sql` §3 validation block |
| Identity model | **organisation membership only** — no consultant/grant branch, no staff branch, no entity branch, no viewer distinction | the predicate above; baseline OP-14 re-verified here |
| Prefix model | `uploads/` only, second segment cast to `uuid` | the predicate above |
| Practical reach | the storage layer knows **less** than the database layer: it cannot express a consultant grant at all | §6.2 vs §6.3 |

### 6.4 The five access questions, answered by evidence

| Access question | Application layer | Database RLS layer | Storage RLS layer | Combined status |
|---|---|---|---|---|
| **Customer access** to client-org documents | `require_org_member()` + `ensure_org_access` (viewer read-only for upload) | `_tenant_select` via `is_org_member`; writes member-only | `d32_documents_*` via active membership | **ALLOW — implemented in all three layers** |
| **Consultant access** to a client's document **rows** | Allowed on the consultant surface (list/upload); `can_upload_documents` required for upload | Allowed — `is_org_consultant` in `_tenant_select`; **writes denied** to consultants | Not applicable (service-role only) | **ALLOW (read) / ALLOW-IF-PERMISSION (upload)** |
| **Consultant access** to document **content** | **No route exists**: no `signed_url`/download endpoint in `api/v3_consultants.py`; the customer route requires `require_org_member()` → a consultant is refused | n/a (app-level) | **DENY** — the predicate has no consultant branch | **NOT ESTABLISHED / effectively denied** |
| **Cross-consultant access** (Firm Y → Client A's docs uploaded by X) | Denied: `_checked_client` is firm-keyed (404 cross-firm) and grants are firm-scoped | Denied: `is_org_consultant` requires Y's own firm to hold the grant | Denied (no consultant branch at all) | **DENY — implemented** |
| **Revoked consultant access** | Denied: `ensure_consultant_org_access` requires `status = 'active'` (403) | Denied: `cc.status = 'active'` is a conjunct of `is_org_consultant` | n/a (already denied) | **DENY — implemented; takes effect immediately on the next request** |
| **Client access to a consultant-created document** | Allowed — the row is an ordinary org-scoped `organization_files` row (Q6) | Allowed via `is_org_member` | Allowed via membership | **ALLOW — implemented (a consequence of Q2, not a separate rule)** |

Tests that guard these boundaries: `test_storage_security.py` (`test_signed_url_org_member_allowed`,
`test_signed_url_cross_org_denied`, `test_signed_url_unknown_document_404`),
`test_v3_consultants.py` (`test_cross_client_document_access_denied`,
`test_consultant_upload_cross_firm_denied`, `test_consultant_upload_requires_upload_permission`),
`test_p6_1b_membership_workspace_authorization.py` (customer/consultant/PE surface separation,
forged-id bypass, `test_multiple_active_firms_ambiguous_denied`, inactive grant),
`test_scope_aware_authorization.py` (`test_c_ensure_org_access_denies_entity_staff`,
`test_e_…allowed`, `test_f_…inactive denied`, `test_g_…cross-firm denied`),
`test_p6_2a_consultant_processing_authorization.py`, `test_d19_lifecycle.py`,
`test_consultant_revocation_migration.py`, `test_legacy_upload_idor.py`,
`test_v3_rls_behavior.py` (integration, real RLS).

---

## 7. Conflicts

Recorded, **not** reconciled (governance rule 13). Each entry: what A says, what B says, why they
cannot both be true, and where.

**C-1 — "No unique constraint on `consultant_clients(consultant_id, organization_id)`" vs the schema.**
* A (T7): `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/research/carbontally_dim02_rules_search_reporting.md`
  finding **A6**: *"`consultant_clients(consultant_id, organization_id)` is a many-to-many join with
  **no unique constraint on (consultant_id, organization_id)** — the same consultant can be linked
  twice to the same org."*
* B (T2/T3): `ENV-LOCAL` and `ENV-LIVE` both have
  `consultant_clients_consultant_id_organization_id_key UNIQUE (consultant_id, organization_id)`;
  `supabase/migrations/00000000000000_init_schema.sql` declares `UNIQUE (consultant_id,
  organization_id)`; `database/rc1/002_rc1_constraints.sql:311-312` creates
  `consultant_clients_consultant_org_uniq`.
* Irreconcilable: the constraint exists. Note A6's **second** clause ("nothing prevents conflicting
  dual-consultant engagements on one org") is **correct** and *is* the Q1 finding — the report is
  only wrong about which constraint is missing. Consequence: A6 must not be quoted as evidence that
  duplicate links are possible, and its "same consultant linked twice" claim is false.

**C-2 — `Final_Kimi` A5 vs schema reality on upload identity.**
* A (T7): A5 recommends adding `file_checksum` (SHA-256) + a unique index and asserts *"No content
  hash anywhere"*.
* B (T3): `customer_documents.file_checksum TEXT` **does exist**
  (`00000000000000_init_schema.sql:607`; `20260806000000_rc2_verification.sql:89` asserts a NULL-safe
  check on it), while `organization_files` has none — and `file_checksum` is never written by any
  Python module (`grep file_checksum backend/` → no non-test hit).
* Irreconcilable as written. Operative truth for storage: **no content identity is populated on the
  document/object path** (Q7), and A5's recommendation is **not** a CarbonTally decision.

**C-3 — Retention matrix vs retention enforcement for storage objects.**
* A (T6): `CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md` §2 row 2 places
  *"Uploaded source documents (`organization_files` + `storage.objects`)"* in one CONFIGURABLE
  (`document_retention_days`) domain.
* B (T4): `backend/services/retention.py:98-110` calls `files.expire_documents_older_than(cutoff)`,
  which only sets `organization_files.deleted_at`; **no** object is ever removed, and `retention.py`
  never touches storage.
* Irreconcilable: either the object belongs to the retention domain (enforcement incomplete) or it
  does not (matrix imprecise). Not reconciled here.

**C-4 — Live namespace vs documented namespace.**
* A (T3/T6): the D32 migration and the demo-lab document describe the object-path layout as
  `uploads/<org_id>/<date>/<file>`.
* B (T2): `ENV-LIVE` holds 44 of 58 objects under `manual_review/…` and `batches/…` — prefixes
  produced by **no** code path traced in this review (P6).
* Irreconcilable: the documented layout does not describe the population that exists.

**C-5 — Storage-RLS prefix scope vs the object population.**
* A (T3): the D32 predicate authorises only `foldername[1] = 'uploads'`.
* B (T2): 76 % of live objects are outside that prefix, and two live second segments (`unknown`,
  `mock-org-id`) are not UUIDs, so the `::uuid` cast would error rather than not-match.
* Irreconcilable as a security statement: the direct-access path authorises a subset; the
  application path (service role) authorises everything.

**C-6 — No firm provenance on the uploaded document.**
* A (T1/T3): **D7** requires durable consultant-firm provenance, server-derived and write-once, and
  implements it on `manual_extraction_items.consultant_firm_id`.
* B (T3/T4): `organization_files` has **no** firm column (26 columns, `ENV-LOCAL`
  `information_schema.columns`), and the consultant upload writes only
  `uploaded_by = current_user.user_id`.
* Irreconcilable for the *object*: after a membership change the firm behind an existing object is
  not derivable from stored data — and D7's own rationale (*"derivation from membership is NOT
  audit-safe"*) applies to documents too.

**C-7 — `report-artifacts` mandated vs absent.**
* A (T1/T3): the frozen artefact is mandatory at finalisation and the bucket name is constrained by
  `CHECK (storage_bucket = 'report-artifacts')`.
* B (T2/T6): the bucket does not exist in either probed environment; `D-11` decided *operational*
  provisioning, no migration creates it, no `create_bucket` call exists, and the provisioning
  document records "not performed".
* Irreconcilable in **state**, not in decision: the decision is closed, the execution is missing.

**C-8 — Storage limits: three different numbers.**
* A (T3/T4): `CT-FINAL-01` ratified 10 MB / 50 files / 500 MB (`utils/upload_limits.py`, enforced per
  ingress), with the storage-layer tightening **pending** (`20261024000000_…`).
* B (T2): `ENV-LIVE documents.file_size_limit = 2 097 152` (2 MiB) — the effective ceiling for direct
  storage writes today, an order of magnitude below the ratified cap.
* C (T4): `routes/organizations/files.py:764` hard-codes a **5 000 MB** org storage limit and
  `routes/admin/dashboard.py:699` hard-codes **50 GB** ("example"); neither is derived from the
  organisation's plan `included_storage_bytes`.
* Irreconcilable: three incompatible limit models (ratified application cap / live storage cap /
  legacy hard-coded quota).

**C-9 — Legacy public-URL construction on a private bucket.**
* A (T1): D32 — *"the documents bucket is PRIVATE. Only short-lived signed URLs are ever produced —
  never a public URL."*
* B (T4): `routes/upload.py:494` (`/api/repair-pdf` returns the URL to the caller),
  `routes/upload.py:718` and `routes/organizations/files.py:594` still call `get_public_url()` on the
  `documents` bucket; both routers are mounted (`backend/main.py:213, 255`).
* Irreconcilable: previously recorded as baseline F-4 and **re-verified here by tracing the code**.

**C-10 — Consultant content access: layers disagree.**
* A (T3/T2, database layer): consultants **may** read org-scoped document rows (`is_org_consultant`
  in `_tenant_select`).
* B (T4/T2, application + storage layers): no consultant route returns document content, and
  `d32_documents_*` grants nothing to consultants.
* Irreconcilable as a single posture: the same principal is simultaneously "authorised to see the
  metadata" and "unable to obtain the bytes".

**C-11 — Architecture documents superseded by the migration chain.**
* A (T6): `CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` §37.2/§37.3/§37.7 states that
  `is_org_consultant`, `ensure_consultant_org_access` and `DELETE /clients/{id}` **ignore**
  `consultant_clients.status`, that *"the current model cannot revoke access"*, and that
  `client_access` is a co-equal grant source.
* B (T3/T4): `20260821000000_d20_d15_active_consultant_grant.sql` made `status = 'active'` a conjunct
  of `is_org_consultant`; `ensure_consultant_org_access` enforces it; D19/D27 added
  `suspended/ended` + `/end`/`/suspend`/`/reactivate`; WS6 restricted revocation roles; and
  `client_access` **no longer** grants organisation access.
* Irreconcilable as current fact: §37.3/§37.7 are stale for those specific clauses. **Not affected:**
  §37.3's statement about *multiple grants* (used for Q1) and the constraint it cites — T2 confirms
  the constraint is unchanged.

**C-12 — Baseline OP-14 / F-1 re-verified (no contradiction).**
Recorded for completeness: this review independently reproduced the live prefix distribution
(`manual_review` 38 + `uploads` 14 + `batches` 6 = 58, of which D32 covers only the 14 `uploads/*`
paths) and re-read the predicate from the catalogue. The baseline finding stands — noted here so the
PO can see it was **re-verified**, not merely copied forward.

---

## 8. PO Decisions Still Required

Only items that **cannot** be answered from existing CarbonTally evidence are listed. Everything in
§1.1 and §5.2 is deliberately **excluded** (governance rules 14/15).

| # | Decision required | Why existing evidence does not answer it | Inputs the PO has |
|---|---|---|---|
| **1** | **Must a consultant-originated upload be physically distinguishable from a customer-originated upload?** | No document decides whether the *origin* of an upload must exist in the storage key. The only decided "who" is the owning organisation (Q2), and the code deliberately funnels both origins through one key shape (§5.1 P1). | Client-org ownership is absolute (D2 §24); firm provenance exists for *processing items* (D7) but not for objects (C-6); one shared prefix today. |
| **2** | **If yes, what is the key shape** — the provisional `consultant/{CONSULTANT_ID}/client/{CLIENT_ID}/…`, a `customer/…` counterpart, an attribute (DB/metadata) instead of a path segment, or another model? | Neither the provisional path nor any alternative is established anywhere in the repository (0 grep matches — §5.3). | The provisional input; the D32 prefix convention; the fact that the D32 storage predicate would need a matching change (C-5, C-10). |
| **3** | **Is multi-firm service of one client intended, and if so must exclusivity or a handover workflow be enforced?** | The schema *permits* multiple grants and two sources *anticipate* the case (§4.2), but no decision says it is desirable; §37.3 records *"no exclusivity or handover enforcement"* as an `ARCHITECTURAL GAP`. | §37.3 / §37.4(c); IV-N2; FIN-06 firm-keyed scope vocabulary; the absence of any constraint on `organization_id`. |
| **4** | **Object-level disposition when a consultant-client grant is revoked, or when an organisation offboards** — retain / archive / reassign / delete / move? | D15 decides only that access ends and that termination is not an ownership claim; §37.5 is titled *"Data preservation requirements (ARCHITECTURAL GAP / NOT SUPPORTED)"*; no code path exists (§3.2). | D15 §37.7 items 1–5 (relationship ≠ ownership; "client leaves" and "platform suspension" are separate states); §37.6 (no full-org export exists). |
| **5** | **Duplicate-upload identity for documents** — require a content hash, and if so with dedupe, warning, or provenance-only semantics? | Nothing is established (§3.1 Q7; C-2). The existing SHA-256 precedents (`calculation_snapshots.content_hash`, `import_batches.source_checksum`, `report_version_artifacts.content_sha256`, `disclosure_value_evidence.payload_hash`) are all different domains, and the `file_checksum` recommendation is third-party advice. | Kimi A5 (recommendation only); the four in-repo SHA-256 precedents. |

| **6** | **Does storage entitlement gain a consultant-firm dimension, and which limit model is authoritative?** | Organisational entitlement is decided (§3.1 Q9), but nothing establishes a firm-level quota, and the two legacy hard-coded quotas (5 000 MB / 50 GB) contradict both each other and the plan model (C-8). | `billing_plans.included_storage_bytes`; `usage_tracking.total_storage_bytes`; `billing_commercial_config['storage']`; `consultant_profiles.organization_id` (firms now have an org identity but no entitlement); FIN-06 as the platform's preferred scoping vocabulary. |
| **7** | **Should direct (user-JWT) storage access ever extend to consultants — and should it cover the prefixes that actually exist?** | The D32 predicate has no consultant branch and covers one of five prefixes (C-5/C-10). Whether that is the intended end state is not stated anywhere; the baseline records it as OP-14 without a decision. | The D32 predicate; the live prefix distribution; the fact that all application I/O uses the service role and therefore bypasses storage RLS. |
| **8** | **Is an upload audit and/or a download/access audit required for documents?** | "No audit on upload / no audit on signed-URL issuance / no deletion audit" is *observed*, not *decided*. The only ratified analogues are D33.1 (evidence drill-down) and the FIN-06 pattern of reusing the existing `audit_logs` infrastructure (§3.4). | D33.1; `repos.audit.record` infrastructure; the `access_count`/`last_accessed` columns that exist but are never written. |
| **9** | **What retained duration applies to `document_retention_days` (and, if desired, an artefact policy under `B4-D8`)?** | The *mechanism* is closed (N3 / CT-FINAL-01), but the *value* is a documented PO/commercial choice: the setting ships unset ("not configured"), the retention document states *"a number cannot be chosen by an engineer"* for the analogous domains, and `B4-D8` is itself recorded as an open PO decision. | The CT-FINAL-01 purpose-based matrix and its Companies Act 2006 / HMRC justification patterns. |

**Deliberately NOT in this list** (already decided — rules 14/15): the two buckets and their privacy;
the artefact key layout; signed-URL-only access and TTLs; the `documents` bucket application cap of
10 MB/50/500 (only its *unapplied storage-layer* tightening is an execution item, not a decision);
the existence of organisation-level entitlement; soft-delete-only retention; the never-purge set;
viewer read-only as a rule; the client organisation as data owner; who may revoke a grant; and the
D32 policy set itself.

**Execution items (not decisions).** Recorded so the PO's review can distinguish "undecided" from
"decided but not done": (i) apply `20261024000000_ct_final_01_documents_bucket_size_limit.sql` so the
storage-layer cap matches the ratified 10 MB (`ENV-LIVE` is at 2 MiB); (ii) provision `report-artifacts`
per `D-11` before any report is finalised in that environment; (iii) retire or align the residual
`get_public_url()` call sites (F-4 / C-9) and the two hard-coded storage quotas (C-8).

---

## 9. Exact Evidence References

### 9.1 Live probe log (`LIVE — READ-ONLY VERIFIED`)

Environment identifiers and counts only; no secrets, no row payloads.

| Probe | Statement class | Result |
|---|---|---|
| `ENV-LOCAL` identity | `select current_database(), version()` | `ct_local_93d5cdd`, PostgreSQL 17.6 |
| `ENV-LOCAL` grant indexes | `pg_indexes` on `public.consultant_clients` | `consultant_clients_consultant_id_organization_id_key` **UNIQUE (consultant_id, organization_id)**; `consultant_clients_consultant_org_uniq` (same columns, from RC1 constraints); `consultant_clients_pkey`; `idx_consultant_clients_lifecycle (consultant_id, status)` |
| `ENV-LOCAL` grant data | `count(*)`, `count(DISTINCT consultant_id)`, `count(DISTINCT organization_id)` | 3 rows / 3 firms / 3 orgs |
| `ENV-LOCAL` storage policies | `pg_policies where schemaname='storage' and tablename='objects'` | exactly 4: `d32_documents_{select,insert,update,delete}_org_member`, all `{authenticated}` |
| `ENV-LOCAL` tenant policies | `pg_policies … tablename in ('organization_files','customer_documents')` | 4 policies each (`_tenant_select/insert/update/delete`), all `{authenticated}` |
| `ENV-LOCAL` document columns | `information_schema.columns` on `public.organization_files` | 26 columns; **no** checksum/hash column; includes `path`, `bucket`, `uploaded_by`, `is_active`, `deleted_at`, `access_count`, `last_accessed`, `status`, `metadata` |
| `ENV-LOCAL` document constraints | `pg_constraint` on `public.organization_files` | only `organization_files_pkey`, `organization_files_organization_id_fkey` (CASCADE), `organization_files_size_bytes_check` |
| `ENV-LOCAL` buckets | `select id,name,public from storage.buckets` | `documents` (public = f) — only |
| `ENV-LIVE` grant indexes | `pg_indexes` on `public.consultant_clients` | `consultant_clients_consultant_id_organization_id_key` (UNIQUE pair), `consultant_clients_pkey`, `idx_consultant_clients_lifecycle` |
| `ENV-LIVE` grant data | aggregate counts | 0 rows (no grants exist in this environment) |
| `ENV-LIVE` buckets | `select name, public, file_size_limit from storage.buckets` | `documents` / `f` / **2 097 152**; **no `report-artifacts`** |
| `ENV-LIVE` storage policies | `pg_policies` (storage.objects) | exactly the four `d32_documents_*`, `{authenticated}` |
| `ENV-LIVE` predicate | `pg_policies.qual` for `d32_documents_select_org_member` | `bucket_id='documents' AND foldername(name)[1]='uploads' AND foldername(name)[2]::uuid IN (select organization_id from organization_members where user_id=auth.uid() and is_active=true)` |
| `ENV-LIVE` object distribution | `group by bucket_id, split_part(name,'/',1), split_part(name,'/',2)` | `documents/manual_review/<org>` 31; `documents/uploads/<org>` 8; `documents/batches/<org>` 6; `documents/manual_review/mock-org-id` 5; `documents/uploads/<org>` 3 + 3; `documents/manual_review/unknown` 2 → **58 objects, 14 under `uploads/`** |

Read-only confirmation: every statement was a `SELECT` over catalogue views or aggregate functions;
no DDL, DML, `CREATE`, `ALTER`, `DROP`, `GRANT`, bucket or object operation was issued in either
environment.

### 9.2 Migrations referenced (path → heading / purpose)

| Migration | Heading / purpose | Used for |
|---|---|---|
| `supabase/migrations/00000000000000_init_schema.sql` | baseline schema | `consultant_clients` (+ inline `UNIQUE (consultant_id, organization_id)`), `consultant_profiles`, `consultant_firm_members`, `organization_files` (541-568), `customer_documents` (572+), `usage_tracking` (1480-1493), `consultant_billing` (1618), `system_settings` retention columns (2077-2079) |
| `supabase/migrations/20260803000000_rc2_rls.sql` | "RC2 RLS" — tenant policy generator + `is_org_consultant` | §3 tenant loop (`_tenant_select` with `is_org_consultant`), §4 `organizations_org_select`, grant policies (323-365) |
| `supabase/migrations/20260821000000_d20_d15_active_consultant_grant.sql` | "D15 (APPROVED 2026-08-20) — consultant access is based on an ACTIVE consultant-client authorization" | `is_org_consultant` requires `cc.status = 'active'`; `client_access` no longer grants org access |
| `supabase/migrations/20260822010000_d27_d19_customer_lifecycle.sql` | "D19 final commercial model (APPROVED 2026-08-20)" | `suspended_at`/`ended_at`/`ended_by`/`lifecycle_updated_at`; `COMMENT ON COLUMN status` (authorised only when `active`); `idx_consultant_clients_lifecycle`; `organizations.organization_type` |
| `supabase/migrations/20260823000000_d32_private_documents_storage.sql` | "D32 (P0) — PRIVATE document storage" | bucket `public = FALSE`; the four approved policies + fail-closed validation; canonical prefix `uploads/` |
| `supabase/migrations/20260824020000_d37_0_billing_security_and_configurable_subscription.sql` | "D37-0 — Billing security remediation + configurable subscription foundation" | `billing_plans.included_storage_bytes`; `billing_commercial_config` incl. `storage` (seed 269-275); write lock-down of `usage_tracking`/`customer_subscriptions` |
| `supabase/migrations/20260831040000_consultant_revocation_roles.sql` | "WS6 / SEC-0003 — Consultant-client revocation role model" | `is_consultant_firm_revoker`; `cc_delete_own_firm`; `consultant_clients_tenant_delete` → owner/admin; revocation preserves provenance |
| `supabase/migrations/20260910120000_p6_2d_consultant_provenance.sql` | "P6-2D — Consultant firm provenance + durable processing-mode provenance (D7)" | `manual_extraction_items.consultant_firm_id` (write-once, no backfill, FK `SET NULL`) |

| `supabase/migrations/20260919000000_p8_b4_frozen_artefact.sql` | "P8 B4 — `public.report_version_artifacts`" | bucket `CHECK`, derived key `CHECK`, `UNIQUE (report_version_id)`, SHA-256 `CHECK`, append-only RLS |
| `supabase/migrations/20260924000000_p8x_x2_operational_telemetry_retention.sql` | "PX-7 Option (a) APPROVED — telemetry retention 90 days" | `operational_telemetry_retention_days`; explicit never-touch list (65-68) |
| `supabase/migrations/20260927000000_p8_fin06_manual_processing_governance.sql` | "FIN-06 — manual processing governance" | scope vocabulary `organization / consultant_firm / consultant_client` (67-82) |
| `supabase/migrations/20261010000000_p17a_accounting_dimensions_and_factor_governance.sql` | "P17-A §6 — `consultant_profiles` ↔ organization linkage (ARCH-06 HIGH-01)" | `consultant_profiles.organization_id` ("the organization that IS this consultant firm"), FK `ON DELETE SET NULL`; `organizations.organization_type` CHECK |
| `supabase/migrations/20261024000000_ct_final_01_documents_bucket_size_limit.sql` | "CT-FINAL-01 storage-layer alignment" | ratified 10 MB storage cap — **not applied** in `ENV-LIVE` |
| `database/rc1/002_rc1_constraints.sql` (311-312), `database/rc1/004_rc1_rls.sql` (120-175), `database/rc2/004_rc2_rls.sql`, `database/rc2/007_rc2_verification.sql` (237) | RC1/RC2 constraint + RLS source sets | `consultant_clients_consultant_org_uniq`; tenant table list including `organization_files` / `customer_documents` |

### 9.3 Code paths (file → function / route)

| File | Function / route | Used for |
|---|---|---|
| `backend/api/consultant_auth.py` | `_resolve_context`, `resolve_consultant_context`, `require_consultant`, `ensure_consultant_permission`, `ensure_consultant_revocation_authority`, `resolve_consultant_firm_id`, `ensure_consultant_org_access`, `ensure_consultant_processing_authorized`, `ensure_consultant_review_authorized`, `ensure_consultant_submission_authorized` | Q1 (firm-keyed chain, single-firm ambiguity), Q3, Q5, §6.1 |
| `backend/api/v3_documents.py` | `create_document_and_enqueue` (path 288, upload 304, `file_url` metadata 314-319), `upload_document` (`POST /uploads`, viewer check 212-231), `_extract_document_text`, `get_document`, `get_document_signed_url`, `document_emissions` (D33.1 audit 632-680) | Q4, Q6, Q7, Q10 |
| `backend/api/v3_consultants.py` | `client_documents` (1251), `upload_client_document` (1274), `_authorized_client_org` (1141), `_checked_client`, `end_client` (716), `suspend_client` (689), `reactivate_client` (743), `delete_client` (879), `add_team_member` (962) | Q1, Q3, Q5, Q6, §6.1 |
| `backend/api/dependencies.py` | `ensure_org_access` (163-193) | §6.1 |
| `backend/api/v3_billing.py` | entitlement + storage endpoint (102-106) | Q9 |
| `backend/api/v3_emissions.py`, `backend/api/v3_evidence.py`, `backend/api/v3_disclosure.py` | signing sites 405-463, 154-192, `get_frozen_artefact_signed_url` | Q10 signed URLs |
| `backend/services/storage.py` | `DOCUMENTS_BUCKET`, `SIGNED_URL_TTL_SECONDS = 3600`, `path_from_url`, `storage_signed_url`, `signed_item` | Q10, §5 |
| `backend/services/retention.py` | `_ELIGIBLE_DOMAINS`, `_TELEMETRY_EXCLUDED_TABLES`, `build_policy`, `compute_expired`, `enforce_retention`, `telemetry_excluded_tables` | Q10 retention |
| `backend/services/billing.py` | `get_entitlement` (87-148), `ensure_processing_entitlement` (167-190), `_consultant_capability_from_plan` (~824-860) | Q9 |
| `backend/data/organization_files.py` | `_FILES_COLUMNS` (15), `delete` (25-29), `expire_documents_older_than` (150-177), `update_metadata` | Q7, Q10 |
| `backend/data/consultants.py` | `get_active_memberships_by_user` (298), `list_clients` (362), `get_client_by_org` (370), `transition_client_lifecycle` (389), `list_active_client_grants` (440), `list_engagements_for_org` (450), `add_client` (469) | Q1, Q3 |
| `backend/routes/upload.py` | `/api/repair-pdf` (`repaired_pdfs/…`, `get_public_url` 486-494), `/api/upload` (`uploads/…` 703, `get_public_url` 718) | §5 producers, C-9 |
| `backend/routes/organizations/files.py` | `get_organization_upload_path` (115-129), upload (580), bulk (865), download (390-425), `DELETE /{file_id}?permanent=` (437-475), storage-limit stub (764) | §5 producers, Q10 deletion, C-8 |
| `backend/routes/admin/dashboard.py` | hard-coded 50 GB storage limit (699) | C-8 |
| `backend/utils/upload_limits.py` | ratified caps + `resolve_policy` / `enforce_single_file` | §5.2 |
| `backend/main.py` | `include_router` for `upload.router` (213) and `files.router` (255) | §5 producers |

### 9.4 Schema / table / constraint references

| Object | Reference | Used for |
|---|---|---|
| `public.consultant_clients` | `UNIQUE (consultant_id, organization_id)` → `consultant_clients_consultant_id_organization_id_key`; FKs to `consultant_profiles(id)` and `organizations(id)`, both `ON DELETE CASCADE`; `status` / `suspended_at` / `ended_at` / `ended_by` / `relationship_origin` | Q1, Q3, §4 |
| `public.consultant_firm_members` | `firm_id`, `user_id`, `role`, `can_manage_clients`, `can_upload_documents`, `can_generate_reports`, `can_manage_team`, `client_access uuid[]`, `is_active` | Q1, §4.1 |
| `public.consultant_profiles` | `user_id`, `is_active`, (P17-A) `organization_id` | §4, Q9 |
| `public.organization_files` | `organization_id` FK (CASCADE), `path`, `bucket`, `uploaded_by`, `is_active`, `deleted_at`, `size_bytes CHECK ≥ 0`, `access_count`, `last_accessed`, `metadata` — **no** checksum column, **no** unique on `path` | Q2, Q6, Q7, Q10 |
| `public.customer_documents` | `organization_id`, `file_checksum TEXT` (unused) | C-2 |
| `public.report_version_artifacts` | `UNIQUE (report_version_id)`, `CHECK storage_bucket='report-artifacts'`, `CHECK` derived `object_key`, `CHECK content_sha256 ~ '^[0-9a-f]{64}$'`, `CHECK byte_size > 0` | Q8 |
| `public.manual_extraction_items` | `consultant_firm_id` FK `SET NULL` (D7), `processing_mode`, `consultant_provenance_at` | §4.3, C-6 |
| `public.usage_tracking` | `organization_id`, `total_storage_bytes`, `UNIQUE (organization_id, usage_month)` | Q9 |
| `public.billing_plans` / `billing_commercial_config` / `customer_subscriptions` / `consultant_billing` | `included_storage_bytes`; versioned `storage` config; org-scoped subscription; legacy consultant billing (no storage column) | Q9 |
| `public.system_settings` | `audit_log_retention_days`, `data_retention_days`, `document_retention_days`, `backup_retention_days`, `operational_telemetry_retention_days` (90) | Q10 retention |
| `storage.buckets` / `storage.objects` | bucket `documents` (private; live `file_size_limit` 2 097 152); four `d32_documents_*` policies | §5, §6.3 |
| Functions | `is_org_consultant(uuid)`, `is_org_member(uuid)`, `is_org_admin_or_owner(uuid)`, `is_consultant_firm_revoker(uuid)`, `p8_disclosure_is_org_member/admin(uuid)` | §6 |

### 9.5 Tests referenced (path → test name)

| Test file | Test(s) | Used for |
|---|---|---|
| `backend/tests/unit/api/test_storage_security.py` | `test_path_from_url_handles_bare_path`, `…_extracts_from_public_url`, `…_extracts_from_signed_url`, `test_signed_url_org_member_allowed`, `test_signed_url_cross_org_denied`, `test_signed_url_unknown_document_404` | §6.4 signed URLs |
| `backend/tests/unit/api/test_ct_final_01_upload_limits.py` | `test_ratified_platform_caps_are_the_documented_ceilings`, `test_resolve_policy_fails_closed_to_the_defaults`, `test_v3_document_upload_enforces_the_effective_limit_before_storage`, `test_legacy_upload_route_rejects_a_foreign_organization`, `test_no_ingress_hard_codes_a_limit`, `test_documents_bucket_size_limit_migration_pins_the_ratified_cap` | §5.2, C-8 |
| `backend/tests/unit/api/test_v3_consultants.py` | `test_cross_client_document_access_denied`, `test_consultant_upload_cross_firm_denied`, `test_consultant_upload_requires_upload_permission` | Q5, Q6, §6.4 |
| `backend/tests/unit/api/test_p6_1b_membership_workspace_authorization.py` | `test_multiple_active_firms_ambiguous_denied`, `test_inactive_membership_denied`, `test_revoked_membership_denied_on_fresh_evaluation`, `test_forged_firm_or_org_id_cannot_bypass`, `test_consultant_cannot_reach_operations_surface`, `test_consultant_cannot_reach_pe_surface` | Q1 (opposite direction), §6.4 |
| `backend/tests/unit/api/test_scope_aware_authorization.py` | `test_c_ensure_org_access_denies_entity_staff`, `test_e_consultant_active_client_allowed`, `test_f_consultant_inactive_client_denied`, `test_g_consultant_cross_firm_client_denied`, `test_f_ensure_consultant_org_access_denies_inactive`, `test_l_entity_staff_denied_consultant_surface` | Q3, Q5, §6.4 |
| `backend/tests/unit/api/test_d19_lifecycle.py` | `test_transition_table`, `test_invalid_transition_denied`, `test_suspend_client`, `test_end_client`, `test_reactivate_client`, `test_lifecycle_transition_requires_manage_clients`, `test_ended_grant_loses_client_access` | Q3 |
| `backend/tests/unit/api/test_consultant_revocation_migration.py` | `test_revoker_helper_is_role_based`, `test_cc_delete_own_firm_uses_revoker`, `test_tenant_delete_restricted_to_org_admin_or_owner`, `test_migration_is_non_destructive` | Q3, §6.1 |
| `backend/tests/unit/api/test_p6_2a_consultant_processing_authorization.py` | `test_consultant_extract_mapping_validate_calculate_allowed`, `test_open_internal_staff_assignment_denies_consultant`, `test_open_pe_assignment_denies_consultant`, `test_forged_or_missing_resource_denied` | §6.1 (D38 conflict / resource scope) |
| `backend/tests/unit/api/test_legacy_upload_idor.py` | `test_batch_progress_denied_for_non_member`, `test_batch_stats_foreign_org_denied`, `test_batch_stats_own_org_allowed` | legacy ingress isolation |
| `backend/tests/integration/test_v3_rls_behavior.py`, `backend/tests/integration/verify_activity_clarifications_rls.py`, `backend/tests/integration/conftest.py` | real-RLS behaviour; tenant table seeding lists (`consultant_clients`, `consultant_profiles`, `consultant_firm_members`) | §6.2 |
| `backend/tests/unit/api/test_document_content_type.py` | content-type renderability on upload (P0-1) | §5.1 P1 |

### 9.6 Documents referenced (path → heading / section relied on)

| Document | Heading / section relied on | Used for |
|---|---|---|
| `docs/architecture/CT-PO-P17-DECISION-01-CAMS-CAPABILITY-APPLICABILITY-CONTRACT-20250925.md` | §5.2 rows 9, 10, 11, 12, 13 (data ownership, actor vs ownership, report/evidence ownership); §5.3 | Q2, Q8, §3.1 |
| `docs/architecture/CT-PO-P17-ARCH-01-SCOPE2-SCOPE3-FULL-ACCOUNTING-CONTRACT-20250925.md` | §57.1 row 7 — *"consultant clients are independent organisations with their own data/evidence/calculations/reporting/audit; consultant access is delegated and client-specific … client-org data ownership and isolation are absolute"* | Q2 |
| `docs/architecture/CT-PO-P17-ARCH-02-RECONCILIATION-20250925.md` | decision table *"Organization (tenant, data owner) — EXISTS — VERIFIED"*; "which organisation owns the data" | Q2, Q9 |
| `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md` | §37.2 (tenancy spine; `consultant_clients` constraints; API chain), §37.3 (multiple grants; gaps), §37.4 (approved direction incl. consultant switch), §37.5 (*"never the data owner"*; data-preservation table), §37.6 (export/import), §37.7 (D15 re-analysis + approved D15 text) | Q1, Q2, Q3, Q4, C-11 |
| `docs/architecture/CarbonTally_V3_Architecture_Specification_v1.0.md` | actor table — *"Customer / Organization: a tenant that owns data (organizations). Data owner; not a processor."*; *"CUSTOMER ORGANIZATION (data owner)"* | Q2 |
| `docs/architecture/CT-FINAL-01-RETENTION-PURPOSE-AND-CONFIGURATION-20260928.md` | §1 (N3 principle), §2 purpose matrix (rows 2, 3–8, 9, 10), §3 justification patterns, §4 what changed, §5 safety guarantees | Q10 retention, C-3, §8 decision 9 |
| `docs/architecture/CARBONTALLY_P6_2F_INDEPENDENT_VERIFICATION_REPORT.md` | NON-BLOCKING finding **IV-N2** (two firms with active grants for one organisation) | Q1, §4.2 |
| `docs/architecture/CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md` | §6.2 (D7 provenance) and the frozen-decision list (*"N3 configurable retention (server-side)"*) | §2, Q10 |
| `docs/operations/REPORT_ARTIFACTS_BUCKET_PROVISIONING.md` | §1 required properties (bucket name, privacy, key, SHA-256, immutability, TTL 300 s "issued after authorization"), §2 procedure, §3 verification, §4 status | Q8, Q10 |
| `docs/cline/reports/P8-FINALIZATION-IMPLEMENT-001.md` | FIN-06 scope vocabulary paragraph (*"no duplicate tenancy concept"*); deferred retention row | Q9, Q10 |
| `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/research/carbontally_dim02_rules_search_reporting.md` | findings **A5** (checksum recommendation) and **A6** (unique-constraint claim) — T7 evidence only | C-1, C-2 |
| `docs/architecture/CARBONTALLY_STORAGE_MANAGEMENT_BASELINE.md` | used as an **evidence index** (F-4, F-12, OP-14, §6.3, §13, C-03/C-05/C-15) — every cited claim re-verified at its underlying source above | C-9, C-12 |

---

## 10. Verification of this artefact

### 10.1 Content completeness

| Required section | Present |
|---|---|
| 1. Executive Summary | §1 (1.1 established / 1.2 undecided / 1.3 asymmetry) |
| 2. Evidence Hierarchy | §2 (T1–T8 with ranking rationale and terminology note) |
| 3. Decision-by-Decision Evidence Matrix (Q1–Q10) | §3.1 (master, 10 rows), §3.2–§3.4 (Q10 classifications) |
| 4. Consultant/Client Relationship Model (forward + reverse) | §4.1, §4.2, §4.3 |
| 5. Storage Namespace Evidence (CURRENT / TARGET ALREADY DECIDED / PROPOSED-UNDECIDED) | §5.1, §5.2, §5.3 |
| 6. Authorization Evidence (customer, consultant, cross-consultant, client→consultant-doc, revoked) | §6.1–§6.4 |
| 7. Conflicts | §7 C-1 … C-12 (no reconciliation attempted) |
| 8. PO Decisions Still Required | §8 rows 1–9 + explicit "deliberately not in this list" |
| 9. Exact Evidence References | §9.1–§9.6 |

### 10.2 Answer summary for the PO (one line each)

```text
Q1  multiple consultant firms per client : ESTABLISHED = YES (schema + predicate + 2 documents; not enforced)
Q2  ownership of consultant-uploaded doc : ESTABLISHED = CLIENT ORGANISATION (firm is never the data owner)
Q3  grant revocation                     : ESTABLISHED = ACCESS REVOCATION ONLY; object lifecycle NOT ESTABLISHED
Q4  customer vs consultant namespaces    : NOT ESTABLISHED (one shared org-scoped prefix today)
Q5  consultant -> customer documents     : CONDITIONAL / CONFLICTING between layers (rows yes, bytes no)
Q6  customer -> consultant-uploaded docs : YES, by construction (indistinguishable rows)
Q7  duplicate upload identity            : NOT ESTABLISHED (no content hash / dedupe)
Q8  report-artefact model                : CLOSED (B4-D5/D6/D7; no consultant id; bucket unprovisioned)
Q9  storage-quota owner                  : ORGANISATION (CLOSED); consultant-level NOT ESTABLISHED
Q10 deletion/retention/audit/signed URLs : PARTIAL overall (see the classification tables in 3.2-3.4)
```

### 10.3 Read-only compliance re-check

| Check | Result |
|---|---|
| Only the one permitted file created/modified | Yes — `docs/architecture/CARBONTALLY_STORAGE_PO_EVIDENCE_REVIEW_20260930.md` |
| Source code / tests / migrations / schema / configuration modified | **None** |
| Database / Supabase modified | **None** — `SELECT`-only probes; no DDL, DML, `GRANT`, bucket or object operation |
| Objects or buckets created, moved or deleted | **None** |
| Implementation code created | **None** — this report is analysis only |
| Ambiguity resolved by inventing a decision | **None** — undecided items are labelled `NOT ESTABLISHED` and listed in §8 |
| Documents reconciled silently with code | **None** — disagreements recorded in §7 |

### 10.4 Final stop condition

```text
STORAGE PO EVIDENCE REVIEW COMPLETE — READY FOR PO REVIEW
```

No implementation, storage-path change, RLS change, authorisation change, migration, Supabase
change, production change, subscription/billing change, bucket creation, object move/delete or test
change was performed. The PO reviews this evidence and then makes or ratifies the Stage 1 decisions
listed in §8.

## END OF STORAGE PO EVIDENCE REVIEW
