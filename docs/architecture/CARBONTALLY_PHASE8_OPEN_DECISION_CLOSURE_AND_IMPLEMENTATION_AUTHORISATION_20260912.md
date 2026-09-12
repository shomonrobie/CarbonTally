# CarbonTally — Phase 8 Open-Decision Closure & Implementation Authorisation

**Prompt ID:** `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-011`
**Date:** 2026-09-12
**Repository HEAD at preparation:** `10d43f65b3354c00a50f4fa584e05ad8baf934e0` (branch `main`)
**Status:** **DECISION PACKAGE / DOCUMENTATION ONLY**
**Implementation authorised by this document:** **NONE — including S1**

---

## 1. Document Purpose and Authority

This package performs three things and nothing else:

1. **Classifies every open decision** inherited from `CT-P8-REPORT-CATALOGUE-RATIFICATION-20260912-010`
   (A1–A15 and A-PE/A-AUD/A-AUD2/A-LEG/A-RLS/A-ROAD/A-ASSUR/A-STAFF/A-COMMENT) into exactly one of
   **DECIDE NOW**, **DEFER WITH EXPLICIT RATIONALE**, **FUTURE PO DECISION** or **IMPLEMENTATION BLOCKER**.
2. **Runs the three required special reviews** (report-table RLS, auditor access, PE access), the
   **report-integrity review**, and the legacy / roadmap / assurance-scoring / staff-capability /
   comment-model analyses.
3. Produces the **final implementation-authorisation matrix** and the **S1 authorisation status**.

**This document does not authorise S1 or any other stage.** It establishes whether S1 *can* be
authorised and on what terms.

**It also reports one material correction** to the previously ratified record (§4). That correction
does not reopen the ratified *direction*; it corrects a *factual statement about current RLS state*
that was wrong.

### 1.1 Evidence standard

Every claim is marked as one of:

| Marker | Meaning |
|---|---|
| **[FACT]** | Verified from the repository (file/line cited) |
| **[INFERENCE]** | Derived from facts, with the reasoning stated |
| **[RECOMMENDATION]** | Architectural advice; not authority |
| **[PO DECISION]** | Requires the Product Owner |
| **[UNVERIFIED]** | Repository evidence insufficient; no inference offered |

---

## 2. Ratified Baseline (Not Reopened)

Accepted from the prior ratified work (`CT-P8-...-008`, `-009`, `-010`) and restated here as the
unchanged premise. Nothing in this package reopens these unless a direct contradiction or
implementation blocker is found — and **none was found**.

| Area | Ratified position |
|---|---|
| Catalogue | `annual` only (12 sections); "80–90 reports" withdrawn; no catalogue expansion |
| Assurance | CarbonTally **supports** assurance; it does **not** audit, verify, certify or opine |
| Auditor boundary | Inspect/comment/find evidence only; **no** edit, **no** approve, **no** finalize; external file editing outside the system of record |
| Content | All 12 engine sections system-controlled; narrative is a bounded allowlist; narrative never alters carbon facts |
| Lifecycle | `GENERATE → DRAFT → REVIEW → APPROVE → FINAL → FROZEN PDF`; six stored states; `EDITED` is an event; approved/final immutable; post-approval change ⇒ new version |
| Approval | Owner + Admin; Member/Viewer never; version-bound; audited; not assurance; PE approval tables must not be repurposed |
| Frozen PDF | One frozen artifact per finalised version; two-hash model (canonical content hash + `pdf_sha256`) |
| AI | Narrative is candidate text only; existing LLM abstraction reused; never computes/factors/invents/writes authoritative data |
| Architecture | One aggregation layer, one report engine, one export/PDF layer, one evidence vocabulary, one authorization contract, one audit ledger, separate conversational domains |

---

## 3. Repository State at Preparation

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `10d43f65b3354c00a50f4fa584e05ad8baf934e0` |
| Relation to origin | 7 commits ahead of `origin/main` (`9e13236…`), **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

**No stop condition was triggered.** No implementation, production access, migration execution or
live RLS testing was required to reach the conclusions below. Two items are explicitly marked
**[UNVERIFIED]** because they require **live database inspection**, which this task must not
perform.

---

## 4. CORRECTION — Report-Table RLS (Special Security Review, Part 1)

### 4.1 What was previously recorded (incorrect)

The Phase 8 discovery, lifecycle specification and ratification all recorded:

> *"No RLS on any report table — no `ENABLE ROW LEVEL SECURITY` and no policy."*

**That statement is inaccurate.** It was produced by grepping for explicit
`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` statements and **missed a dynamic all-tables loop**.

### 4.2 The corrected facts

**[FACT]** `supabase/migrations/00000000000000_init_schema.sql:2315-2324` contains a
**schema-wide RLS enablement block**:

```sql
-- RLS ENABLEMENT (All tables)
DO $$
DECLARE t text;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
END $$;
```

This block runs **near the end of `init_schema.sql`** (line 2315; the file ends at 2328), i.e.
**after** the report tables are created in that same file:

| Report table | Created at | Has `organization_id`? |
|---|---|---|
| `report_templates` | `init_schema.sql:947` | **Yes** (nullable) |
| `report_generation_queue` | `:970` | **Yes** (NOT NULL, FK) |
| `report_versions` | `:1003` | **No** |
| `report_comments` | `:1020` | **No** |

**[INFERENCE]** Therefore **RLS is enabled on all four report tables** (deny-by-default for
`authenticated`/`anon` absent a policy). The explicit `ALTER TABLE … ENABLE ROW LEVEL SECURITY`
statements in later migrations (19 tables, e.g. `calculation_snapshots`, `issues`, `vehicles`,
`billing_*`, `work_item_assignments`) exist **only because those tables were created after** the
init-time loop had already run — consistent with the loop being one-shot.

### 4.3 The real question is policy coverage, not enablement

**[FACT]** `supabase/migrations/20260803000000_rc2_rls.sql` **Section 3** (lines 130-178) applies
tenant policies **dynamically to every `public` table carrying an `organization_id` column**:

```sql
FOR r IN SELECT DISTINCT c.table_name FROM information_schema.columns c
          JOIN pg_tables t ON ...
         WHERE c.table_schema='public' AND c.column_name='organization_id'
           AND c.table_name NOT IN ('organizations','organization_members')
LOOP
   CREATE POLICY <t>_tenant_select ... USING (public.is_org_member(organization_id)
                                              OR public.is_org_consultant(organization_id));
   CREATE POLICY <t>_tenant_insert ... WITH CHECK (public.is_org_member(organization_id));
   CREATE POLICY <t>_tenant_update ... ;
   CREATE POLICY <t>_tenant_delete ... ;
END LOOP;
```

**[INFERENCE]** Applying that rule to the report tables produces a **split** posture:

| Table | `organization_id` | Expected tenant policy from rc2_rls §3 | Effective posture under RLS |
|---|---|---|---|
| `report_generation_queue` | Yes | **Policy created** (org-scoped select/insert/update/delete) | Org-gated for `authenticated` |
| `report_templates` | Yes (nullable) | **Policy created**; global rows (`organization_id IS NULL`) evaluate `is_org_member(NULL)` → not true | Org rows gated; **global rows may be invisible to `authenticated`** |
| `report_versions` | **No** | **No policy possible** | **Deny-all to `authenticated`** |
| `report_comments` | **No** | **No policy possible** | **Deny-all to `authenticated`** |

### 4.4 Why the application works despite deny-all

**[FACT]** The V3 report API reads and writes `report_versions` and `report_generation_queue`
successfully today (`data/reports.py`, `data/report_versions.py`) via the backend's asyncpg
connection.

**[INFERENCE]** If `report_versions` is deny-all to `authenticated` under RLS, the backend must
connect as a role that **bypasses RLS** — a table owner or `service_role`-equivalent — because
owners bypass RLS unless the table is marked `FORCE ROW LEVEL SECURITY`.

**[FACT]** `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` §14 records exactly this gap:
*"FORCE RLS remains a separate security-hardening investigation and is not a prerequisite for
architectural freeze."*

**[INFERENCE]** The accurate model is therefore:

```text
RLS ENABLED (default-deny)         →  yes, on all four report tables
RLS policy coverage               →  org-gated for report_generation_queue / report_templates;
                                     NONE for report_versions / report_comments
Effective enforcement for the API →  likely BYPASSED (owner/service role; not FORCE RLS)
Effective control today           →  API-layer guards only (require_org_member + ensure_org_access)
```

### 4.5 What remains UNVERIFIED

The following require **live database inspection** and were **not** performed (prompt stop
conditions):

| # | Unverified item | Why it does not change the recommendation |
|---|---|---|
| U1 | The **actual** policy list on each report table in the live database (the rc2_rls §3 loop's effect depends on schema state at run time) | The recommendation does not depend on which policies exist; it depends on policy **coverage being incomplete and unrelated to lifecycle semantics** |
| U2 | The **effective role** of the backend's asyncpg connection and whether RLS is bypassed | `[INFERENCE]` above already explains the observed behaviour; the recommendation is to make the posture deliberate either way |
| U3 | Whether `FORCE ROW LEVEL SECURITY` is set anywhere | Blueprint §14 states FORCE RLS is an open hardening investigation, not a freeze prerequisite |

**No live database access, migration execution or RLS testing was attempted.**

### 4.6 Does adding lifecycle functionality create a material security exposure?

**[RECOMMENDATION] Not by itself — but it must not be built on an unexamined posture.**

* S1 adds **no table, no column, no policy, no endpoint** → no change to the security surface.
* Later stages **add writes** to `report_versions` (status, overlay, approval, finalization) and
  **new reads** (version history, comments) — precisely the operations that should be covered by
  more than one control.
* The current split would become **misleading**: a future maintainer could reasonably believe
  `report_versions` is org-protected by RLS when it has **no policy at all** (and is only
  reachable because the connection bypasses RLS).

### 4.7 Is API-layer authorization sufficient as an interim control?

**[FACT]** The API guards are real and server-side: `require_org_member()` +
`ensure_org_access(current_user, report["organization_id"])` on every report route, with
org-isolation negative tests in `backend/tests/unit/api/test_v3_reports.py`
(`test_list_reports_org_isolation_denied`, `test_get_report_org_isolation`,
`test_generate_report_org_isolation`, `test_download_report_org_isolation`,
`test_versions_org_isolation`, `test_get_report_content_org_isolation`).

**[RECOMMENDATION] Yes — acceptable as an interim control for the current surface.** It matches the
platform-wide posture (owner/service-role bypass). It is **not** acceptable as the permanent
posture once lifecycle writes exist.

### 4.8 Must RLS be implemented before report-lifecycle work?

**[RECOMMENDATION]**

| Stage | RLS requirement |
|---|---|
| **S1 — correctness** | **No RLS work.** S1 changes no table, policy or endpoint. |
| **S2 — lifecycle schema** | **RLS work belongs here**, with the migration that adds version state: (a) decide deliberately for `report_versions` / `report_comments` — add `organization_id` to use the existing tenant-policy pattern, **or** document application-level-only authorization; (b) confirm `report_generation_queue` is intentionally org-gated; (c) **weaken nothing**. |
| **S5+ — frozen artifacts** | Storage-object policies must be explicit (the platform already enables RLS on `storage.objects`: `20260823000000_d32_private_documents_storage.sql:21`). |

**Verdict:** report-table RLS is **not an S1 blocker**; it **is an S2 prerequisite**.

### 4.9 Is a documented app-layer-only approach technically defensible?

**[RECOMMENDATION] Yes — but only if it is explicit and governed.**

A deliberate application-level-only model is defensible when: the DB connection bypasses RLS
anyway (owner / service role); authorization is centralised in one guard set; negative tests prove
org isolation; and the choice is **documented** rather than accidental (AGENTS.md §67 permits
elevated access only with explicit application-level authorization and a documented reason).

**What is not defensible** is the *current* state: RLS **enabled but unpolicied** on two tables,
with no documentation of the resulting deny-all-plus-bypass arrangement. That is *accidental*, not
*deliberate*.

**Recommendation:** either **(a)** complete policy coverage using the existing
`organization_id` + `is_org_member` pattern (preferred), or **(b)** formally document the
app-layer-only posture for the two un-policied tables. This is **`A-RLS`** and is a **PO decision**
(a security-architecture call with migration implications).

### 4.10 Correction summary and required downstream edits

| Document | Statement to correct |
|---|---|
| Phase 8 discovery (`-008`) §8.4 / §22.3 | "No RLS on any report table" |
| Lifecycle spec (`-009`) §22.3 | "No RLS on any report table" |
| Ratification (`-010`) §8.4, D-12, defect #1, T2 | "No RLS on any report table" |

**Corrected statement:**

> **RLS is enabled on all four report tables** via the schema-wide RLS enablement loop in
> `init_schema.sql:2315-2324`. Tenant **policy coverage is incomplete**: `report_generation_queue`
> and `report_templates` carry `organization_id` and therefore receive tenant policies from
> `rc2_rls.sql` §3; `report_versions` and `report_comments` have **no `organization_id` and
> therefore no policy**, making them deny-all to `authenticated` under RLS. Backend access
> currently works because the connection role bypasses RLS (not `FORCE`d) — the same posture
> Blueprint §14 records as an open hardening item. **Effective report authorization today rests on
> the API-layer guards.**

**Required edit:** the three prior documents should receive a correction note at their next
revision (a documentation task; **not performed here** — this package is the correction record).

---

## 5. Special Security Review, Part 2 — Auditor Access

### 5.1 Does an auditor role / assurance reviewer role exist?

**[FACT] No.** Repository-wide search for `auditor` / `assurance` in application code returns
**only**:

* Phase 7 **theme names in comments/docstrings** (`backend/data/reporting.py:19-35`,
  `backend/api/v3_reporting.py:370-387`, `frontend/src/v3/admin/AuditTab.jsx:2-8`);
* the **`not_assurance` marker** and `AUDIT_NOT_ASSURANCE_NOTICE` constant
  (`backend/data/reporting.py:30, 106-107, 1192-1193`);
* a comment referencing auditors in `v3_automatic_processing.py:193` and
  `20260807020000_add_calculation_snapshots.sql:9`;
* a Phase 7 migration title
  (`20260912000000_p7_audit_immutability_and_indexes.sql:2`).

**No auditor role, no assurance-reviewer role, no auditor assignment table, no auditor workspace,
no auditor API.** This confirms the Phase 7 closure record: *"no auditor role/table was created"*.

**[FACT]** Existing roles are: organisation roles (`organization_members.role`), consultant firm
roles, staff roles (`staff_roles.name` + JSONB permissions), and PE roles (staff roles × entity
scope). Evidence/audit reads are gated by `ensure_org_audit_access` (owner/admin) and staff
permissions.

### 5.2 Is there a client/report scope mechanism that could safely be extended?

**[FACT]** Yes — the platform already has a **proven, active-grant scoping pattern**:

| Mechanism | Where | Reusable for a reviewer? |
|---|---|---|
| `consultant_clients` + active-grant check (`ensure_consultant_org_access`) | `api/consultant_auth.py` | **Yes** — the closest analogue: an external party scoped to specific organisations with revocation semantics (ACTIVE / SUSPENDED / ENDED) |
| Entity scoping (`require_entity_scope`, `processing_entities`) | `api/operations_auth.py` | Yes, for entity-level reviewer scope |
| `is_org_member` / `is_org_consultant` RLS helpers | `rc2_rls.sql` | Extendable with an `is_org_reviewer`-style helper (future work) |
| `organization_members` invitations/roles | `routes/organizations/members.py` | Pattern for scoped invitation, but **not** appropriate for an external reviewer (would make them an org member) |

**[RECOMMENDATION]** A future reviewer model should mirror the **consultant-grant pattern**
(explicit grant record + lifecycle states + revocation) rather than reusing organisation membership.
This is **not created here** and is **not needed for S1**.

### 5.3 Verdict

* Auditor capability: **does not exist** → the ratified boundary (§2) is a **design target only**.
* It is **`FUTURE`** and **does not block S1 or S2**.
* Creating it requires its own scoped trust model, RLS-aware reads, reviewer-action audit and
  negative tests — a **separate authorisation**, not part of the report-lifecycle baseline.
* **`A-AUD`** (assignment/granting model) and **`A-AUD2`** (finding record type) remain open and
  are **not S1 blockers**.

---

## 6. Special Security Review, Part 3 — PE Access

### 6.1 Current PE/reporting relationships (traced)

**[FACT]** `backend/api/v3_pe.py` (662 lines, 21 routes) contains **zero references to `report`**.
Its routes are: `/me`, `/work`, `/batches/{id}/items`, item `start`/`extract`/`map`/`validate`/
`calculate`/`status`/`pe-review`/`pe-qc`/`clarify`, `/issues`, `/issues/{id}`, `/team`,
`/items/{id}/workspace`, `/items/{id}/work`, and work `claim`/`release`/`complete`.

**[FACT]** PE-adjacent reporting exists only as **operational performance** endpoints:
`GET /api/v3/ops/entities/{id}/performance` and `GET /api/v3/ops/entities/{id}/audit-activity`
(guarded by `require_entity_scope` / staff permissions), plus PE frontend surfaces
(`PEDedicatedHome`, `PEManagerDashboard`, `PeWorkItemsPage`, `PeMessagingPage`).

**[INFERENCE]** PE users therefore have **no route, no scope mechanism and no UI** that could open
a customer report document, report version or final artifact.

### 6.2 Should PE users be allowed to access customer report documents?

**[RECOMMENDATION] No — and no change is required to satisfy the ratified model.**

Reasoning grounded in the architecture:

1. Blueprint §5.3: *"A PE is not a customer. PE staff are not CarbonTally staff. PE Admin is not
   CarbonTally Admin. PE access is entity-scoped and assignment-based."*
2. Blueprint §7/§8 establish the approved PE **privacy and document boundary**.
3. PE work is **processing**, not report consumption; a customer report is a customer deliverable.
4. The ratified `PE Admin reporting` surface (§16 of `-010`) is **portfolio management reporting
   over the PE's own authorised entities** — a different artefact from a customer report document.
5. The lifecycle specification (`-009` §22.2) already records PE report access as **"No"**.

**[RECOMMENDATION]** Keep **PE report-document access = No**, and keep the PE Admin portfolio
reporting surface as the PE-visible management view. **`A-PE` is therefore answerable from
architecture evidence** — but because it is an access-model question, it is classified
**`FUTURE PO DECISION`** for formal confirmation rather than decided here.

**[FACT]** No access change was made.

---

## 7. Special Report-Integrity Review & the S1 Boundary

### 7.1 The three identified correctness issues — reconfirmed

**Issue 1 — `report_versions.is_current` can be multiply-true.**

**[FACT]** `backend/data/report_versions.py:56-90` — `create(..., is_current: bool = True)` inserts
a row with `is_current = TRUE` and **never demotes any prior current row**:

```python
INSERT INTO public.report_versions (report_id, version_number, content, file_url, file_name,
        created_by, notes, change_summary, is_current)
VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9)   -- $9 defaults True
```

**[FACT]** `get_current()` (line 104) masks the symptom:
`WHERE report_id = $1 AND is_current = TRUE ORDER BY version_number DESC LIMIT 1`.

**[FACT]** The unique constraint is only `UNIQUE (report_id, version_number)`
(`init_schema.sql:1014`; index `report_versions_report_version_uniq` at `:2149`) — it does **not**
constrain `is_current`.

**[FACT]** In the current V3 flow a report is generated once, so the defect is **latent, not
active**. It becomes active the moment a second version exists (i.e. exactly what S2+ introduces).

**[UNVERIFIED]** Whether duplicate `is_current = TRUE` rows already exist in the live database.
**This requires live DB inspection, which was not performed.**

**Issue 2 — the report list does not expose `current_version` correctly.**

**[FACT]** `backend/api/v3_reports.py` — `list_reports` returns `shape_report_status(r)` per row,
and `shape_report_status` **does not include `current_version`**. Only `shape_report_out` (used by
the detail route) adds it.

**[FACT]** `frontend/src/v3/reports/ReportsPage.jsx:242-246` renders the "Version" column from
`r.current_version?.version_number || (r.status === 'completed' ? 'v1' : '—')`.

**[INFERENCE]** The column therefore **always** falls back to `v1` (when completed) or `—`; it
never reflects a real version number. A UI accuracy defect — but one that becomes **actively
misleading** once multiple versions exist.

**Issue 3 — `download_report` documentation is stale.**

**[FACT]** The `download_report` docstring states *"no PDF rendering exists in V3 — documented
backend gap"*, while `GET /api/v3/reports/{report_id}/pdf` **does exist** and is exercised by
`test_report_pdf_download_branded` / `test_report_pdf_not_ready`.

**[INFERENCE]** Documentation drift only; no functional defect.

### 7.2 Do these belong to the first implementation stage?

**[RECOMMENDATION] Yes — all three:**

| Issue | Why it belongs in S1 |
|---|---|
| `is_current` invariant | A **correctness defect in the version spine** every later stage depends on. Fixing it after lifecycle states exist means repairing the invariant under live lifecycle data. |
| `current_version` in listing | Trivial code change; the frontend **already expects** the field. Otherwise a lifecycle UI ships on a list payload that cannot report versions. |
| Stale docstring | Zero-risk; prevents future implementers acting on a false premise (it already misled a prior audit). |

### 7.3 Confirm or challenge the S1 boundary

The proposed S1 was:

> **S1 = fix the `is_current` invariant; expose `current_version` in report listing; correct the
> stale `download_report` documentation.** No lifecycle states, no approval, no narrative editing,
> no RLS changes, no frozen PDFs, no auditor workspace, no frontend lifecycle UI, no AI narrative,
> no billing changes.

**[RECOMMENDATION] CONFIRM the boundary — with one clarification and two additions.**

**Clarification — the `is_current` fix has two implementable shapes:**

| Shape | Mechanism | Migration? | Assessment |
|---|---|---|---|
| **S1-A (recommended)** | Repository-level: in **one transaction**, demote prior `is_current` rows for the report, then insert the new row with `TRUE` | **No** | Keeps S1 code-only; no schema authorisation required; **also self-repairs** if duplicates already exist (demote-all, then set one) |
| **S1-B (deferred to S2)** | Structural: partial unique index (`UNIQUE (report_id) WHERE is_current`) | **Yes** | Structurally guarantees the invariant — but index creation **fails if duplicate `is_current=TRUE` rows already exist**, so it may require a data-repair step and is a schema change **outside S1's declared boundary** |

**[RECOMMENDATION]** Deliver **S1-A** now (no migration, no data repair) and register **S1-B** as a
candidate for the S2 schema stage — where a migration is being written anyway and where the
`[UNVERIFIED]` duplicate-row question can be answered by a live check under explicit authorisation.
This keeps S1 code-only while still fixing the invariant.

**Addition 1 — no N+1.** The `current_version` change must fetch current versions for the page in
**one** query (e.g. a single `report_versions` lookup for the returned report ids), not one query
per report — preserving the platform's stated "no N+1" property (`v3_reporting.py` D30 note).

**Addition 2 — test obligation.** Existing tests (`test_list_reports_*`,
`test_generate_report_records_version_history`, `test_report_version_roundtrip`) must keep passing,
and a regression test must assert that after two version creations exactly **one** `is_current =
TRUE` row exists for a report.

### 7.4 What S1 explicitly does NOT do

```text
× lifecycle states / transitions
× approval / review / comments
× narrative editing
× RLS changes
× frozen PDF / artifacts
× auditor workspace
× frontend lifecycle UI
× AI narrative
× billing / entitlement
× any migration
× any data repair
```

### 7.5 Is the S1 boundary internally consistent with the ratified plan?

**[FACT]** Consistent. `-009` §35 and `-010` §23.2 sequence correctness (S1) **before** the schema
stage (S2), and state the principle: *"do not extend a table whose existing invariant is provably
violable."* S1 as bounded above satisfies that principle and introduces no schema, RLS or lifecycle
surface.

---

## 8. Legacy Report Disposition

### 8.1 What is live vs dead

**[FACT]**

| Artefact | Status |
|---|---|
| `backend/api/v3_reports.py` (`/api/v3/reports/*`) | **LIVE** — mounted by `backend/api/router.py` |
| `backend/api/v3_reporting.py` (`/api/v3/reporting/*`, `/api/v3/ops/reporting/*`) | **LIVE** — mounted |
| `backend/api/v3_exports.py` (`/api/v3/exports/*`) | **LIVE** — mounted |
| `backend/engines/report_generation.py`, `engines/pdf_render.py` | **LIVE** — used by the V3 report route |
| `backend/routes/reports.py` (2,097 lines) | **NOT mounted** — the V3 router does not include it |
| `backend/report_generator.py` (1,071 lines, FPDF SECR generator) | **NOT mounted** |
| Legacy admin CRA analytics | **NOT mounted** in the V3 app |

**[INFERENCE]** The legacy reporting surface is **dead code that remains on disk and in repository
history**; it is not reachable through the V3 application.

### 8.2 Must anything be preserved?

**[RECOMMENDATION] Preserve as-is for now.** AGENTS.md §79 requires determining whether legacy
functionality is still referenced, whether it is part of the application contract, and what
deprecation requires. The legacy generator also encodes **SECR narrative concepts** (YoY
comparison, methodology notes, efficiency measures, intensity ratios) that may hold **product
knowledge** worth preserving as a behavioural reference even after the code is retired.

### 8.3 Should the legacy labels remain?

**[RECOMMENDATION] Keep the labels out of the live product; keep them in the repository.**
They must **not** appear in V3 catalogue responses, V3 UI or product copy. They may remain in the
unmounted legacy files until a disposition decision is taken.

### 8.4 Does the legacy live PDF route conflict with the future frozen-PDF model?

**[FACT]** There are **two different PDF producers**:

| Route | Behaviour | Status |
|---|---|---|
| `GET /api/v3/reports/{id}/pdf` | **V3** — renders from persisted `generated_content` + server-authorized brand via `render_branded_pdf`; **not stored** | **LIVE** |
| Legacy FPDF generator (`EnhancedSustainabilityReportPDF`) | In the unmounted monolith | **Not mounted** |

**[INFERENCE]** Only the **V3** live-render route interacts with the future frozen-PDF model. There
is no conflict today (no frozen model exists), but after S5 it becomes ambiguous: a `FINAL` version
must serve the **stored** artifact, not a fresh render. This is exactly **`A15`**. The *legacy
unmounted* generator creates **no** conflict.

### 8.5 Recommendation summary

| Question | Recommendation | Classification |
|---|---|---|
| What is live? | V3 report/reporting/export surfaces only | **[FACT]** |
| What is dead? | `routes/reports.py`, `report_generator.py`, legacy admin CRA analytics | **[FACT]** |
| Preserve? | Yes — keep on disk, unreferenced, as a behavioural ancestor | **[RECOMMENDATION]** |
| Deprecate now? | **No** — requires a dependency inventory and explicit authorisation | **DEFER** |
| Labels? | Keep out of live product; no revival | **[RECOMMENDATION]** |
| Live PDF route conflict? | V3 live-render vs future stored artifact → **`A15`** | **FUTURE PO DECISION** |

**No legacy code was deleted or modified.**

---

## 9. Roadmap Consistency

### 9.1 Comparison against the ratified Phase 8 decisions

**[FACT]** `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (ratified 10 Sep 2026) states:

| Location | Roadmap statement | Discrepancy |
|---|---|---|
| §0 decision 3 | Phase 8 — official roadmap **name** ratified; *"Detailed scope NOT defined; nothing authorized"* | **Stale** — the Phase 8 discovery, lifecycle specification and product ratification have since been produced and accepted |
| §11 (Phase 8 block) | `NOT YET DEFINED` / `FUTURE — ROADMAP NAME RATIFIED; DETAILED SCOPE NOT DEFINED` / `NOT STARTED — NOT AUTHORIZED` | **Stale** — Phase 8 scope is now defined as *Report Versioning & Approval Lifecycle* within Advanced Analytics |
| §13 (Current Project Position) | `CURRENT PRODUCT PHASE: Phase 6 — Consultant Workflow`; `NEXT GATE: P6-2C` | **Stale** — Phase 6 and Phase 7 have closed |
| §14 (Phase Authority Map) rows 7 & 8 | Phase 7 / Phase 8: `FUTURE — NAME RATIFIED; SCOPE NOT DEFINED` | **Stale** — Phase 7 is **CLOSED — independently verified**; Phase 8 is in design with a ratified catalogue/lifecycle/access model |
| §18 items 2 & 3 | *"Phase 7 detailed scope — undefined"*; *"Phase 8 detailed scope — undefined"* | **Stale** for both |
| §18 item 8 | *"the current repository HEAD is `16391217103b98dcea520070c5a22c68f12fe607` … all subsequent Phase 4/5/6 work is uncommitted"* | **Stale** — HEAD is now `10d43f6…`; the work is committed (unpushed) |

### 9.2 Classification of each discrepancy

| # | Discrepancy | Classification |
|---|---|---|
| R1 | §0/§11/§14 Phase 8 "scope not defined / not authorised" | **Documentation-only** for the ratified *name* and sequencing; **PO decision required** to record the Phase 8 design authorisation |
| R2 | §13 current phase still Phase 6 | **Documentation-only** (status table) |
| R3 | §14 rows 7/8 statuses | **Documentation-only** |
| R4 | §18 items 2/3 (scope undefined) | **Documentation-only** |
| R5 | §18 item 8 (stale HEAD / uncommitted claim) | **Documentation-only** |
| R6 | §0 decision 5 authority split (roadmap = sequencing, Blueprint = architecture) | **Consistent — no change needed** |

**[RECOMMENDATION] None of these discrepancies is implementation-impacting.** No roadmap statement
contradicts a ratified Phase 8 decision in a way that would change S1 or S2. They are **status
drift**, not authority conflict: the roadmap was correct when ratified and has not been updated for
subsequent PO-authorised work.

### 9.3 Recommended eventual roadmap updates (not performed)

1. §0 — append a ratification continuation note (Phase 7 closed; Phase 8 entered an authorised
   design sequence: discovery → lifecycle specification → product ratification → open-decision
   closure).
2. §11 — record the Phase 8 defined scope (Report Catalogue, Versioning, Approval Lifecycle, Access
   Model) and status.
3. §13 — update `CURRENT PRODUCT PHASE` / gates.
4. §14 — update rows 7 and 8 (Phase 7 = CLOSED; Phase 8 = IN DESIGN / SCOPE DEFINED).
5. §18 — close items 2 and 3; refresh item 8's HEAD reference.
6. Add an explicit note that **phase-level authorisation for Phase 8 implementation remains
   outstanding**.

**This is `A-ROAD`, classified `PO DECISION REQUIRED` (documentation governance) — it does not
block S1.**

**The roadmap was NOT edited by this task.**

---

## 10. Assurance-Readiness Scoring

### 10.1 Current state

**[FACT]** CarbonTally already has an **evidence-based readiness indicator**, deliberately *not*
called a score: `backend/data/reporting.py` — `audit_readiness_from_counts(...)` returns an
evidence-based readiness summary marked `"not_assurance": True` with `AUDIT_NOT_ASSURANCE_NOTICE`;
the frontend labels it **"AUDIT EVIDENCE READINESS"** (`frontend/src/v3/admin/AuditTab.jsx`).

### 10.2 Assessment

| Question | Assessment |
|---|---|
| Sufficiently defined? | **No** — no methodology exists for a numeric score (weighting, thresholds, category values, data sources, confidence) |
| Legally/product-wise safe? | **[RECOMMENDATION] Not as a numeric *score*.** A "score" invites reading as a quasi-opinion, conflicting with the ratified non-claim (§2; Phase 7 §5) |
| Requires methodology before implementation? | **Yes** — a defensible score needs a published, versioned methodology |
| Risks implying independent assurance? | **Yes — materially.** The existing design avoids this deliberately via *readiness* language plus `not_assurance` |
| Should it be deferred? | **Yes** |

### 10.3 Verdict

**[RECOMMENDATION] `DEFER` — `FUTURE PO DECISION`.**

**Prerequisite definition required before revisiting:**

1. What the score measures (evidence completeness? validation pass rate? provenance coverage?).
2. Weighting and thresholds, and whether it is computable from existing persisted fields only.
3. How it is labelled so it cannot be read as audit, assurance or verification.
4. Whether it is customer-facing or internal-only.
5. Legal review of any customer-facing claim derived from it.

**[FACT]** No score was implemented. **`A-ASSUR`** remains open; **not an S1 blocker.**

---

## 11. Staff Capability Model

### 11.1 Current architecture

**[FACT]** Staff authorization is **capability-based**: `staff_roles.permissions JSONB` +
`staff_profiles.role_id` (`init_schema.sql:1220-1240`), with an existing permission vocabulary in
`backend/domain/staff.py` and `backend/auth.py`:

```text
can_approve, can_delete, can_export, can_extract, can_manage_organizations,
can_manage_roles, can_manage_staff, can_process, can_review,
can_view_all, can_view_organizations
```

**[FACT]** Permission defaults are seeded in `backend/routes/admin/permissions.py`
(`can_approve: True` for some roles, `False` for others). **`can_approve` today concerns
processing/data approval, not report approval.**

### 11.2 Assessment

| Option | Assessment |
|---|---|
| Introduce staff-specific report capabilities **now** | **[RECOMMENDATION] No.** Report approval is the **customer's assertion** (§2). Adding staff report-approval capability now would pre-empt `A2` and risk implying CarbonTally-endorsed content |
| Reuse existing staff capabilities | Partially viable **later**: report *operations* (support visibility, ops reporting) could reuse `can_view_all`/`can_review`. Report **approval/finalization** should not be mapped to an existing flag by default |
| Keep the current lifecycle implementation **customer-only** | **[RECOMMENDATION] Yes** — matches the ratified baseline (Owner + Admin approve; consultant/staff approval PO-gated) |
| Defer explicitly | **[RECOMMENDATION] Yes** |

### 11.3 Verdict

**[RECOMMENDATION] `DEFER` — customer-only for the current lifecycle implementation.**

No new staff capability is required for S1 (no lifecycle surface at all) or S2 (schema only). Staff
capability for report review/approval becomes relevant only when the lifecycle UI and approval
flows are built (S3+), and even then only if the PO decides staff may act. **`A-STAFF` is
`FUTURE PO DECISION`; `A2` (consultant/staff approval) remains the governing PO decision.**

**No authorization code was modified.**

---

## 12. Comment / Finding Model

### 12.1 The existing table

**[FACT]** `report_comments` (`init_schema.sql:1020-1033`, currently **dormant** — zero backend or
frontend usage):

| Column | Suitable for | Gap |
|---|---|---|
| `report_id` | Report-scoped comment | **Not version-scoped** |
| `user_id` | Author | — |
| `section_id` | Section-anchored comment (matches the 12 engine section ids) | — |
| `comment` | Body | — |
| `comment_type` | Classification | **No vocabulary defined anywhere** |
| `is_resolved`, `resolved_at`, `resolved_by`, `resolution_notes` | Resolution lifecycle | — |
| `created_at`, `updated_at` | Timestamps | — |

**Missing for the ratified lifecycle:** `organization_id` (tenant scoping), `version_number` /
`version_id` (version binding), and a `visibility` flag (internal vs shared).

### 12.2 Can it safely serve the five required uses?

| Use | Feasible with `report_comments` + additions? |
|---|---|
| Customer comments | **Yes** — `comment_type` + `visibility = shared` |
| Consultant comments | **Yes** — `visibility = internal` |
| Assurance reviewer comments | **Yes** (once a reviewer identity exists — §5) |
| Findings | **Yes, at first** — a finding is a comment with `comment_type = finding`, `visibility`, and structured metadata |
| Evidence requests | **Yes, at first** — `comment_type = evidence_request` |

**[RECOMMENDATION]** `comment_type` needs a **defined vocabulary**. Suggested minimal set:
`review_note`, `change_request`, `approval_note`, `finding`, `evidence_request`. Structured extras
(severity, due date, linked evidence id) can live in added JSONB metadata rather than a new table
initially.

### 12.3 Is a separate finding table required **now**?

**[RECOMMENDATION] No — not now.**

* `report_comments` already has section anchoring and a resolution lifecycle — the two hardest parts.
* Findings and evidence requests share the same shape as review comments at first (author, target,
  body, resolution state, visibility).
* A separate table would duplicate audit/visibility/resolution concerns and create a **parallel
  structure** — against the ratified anti-duplication rule.
* A dedicated finding model becomes justified only if findings need **independent lifecycle
  states** (open → accepted → disputed → closed with remediation), **severity-based SLA**, or
  **cross-report aggregation** — none of which is in the ratified baseline.

**[RECOMMENDATION] Revisit at the reviewer-capability stage (§5)**, where `A-AUD2` is the governing
decision. **`A-COMMENT` is classified `DEFER WITH EXPLICIT RATIONALE`.**

**No comment or finding implementation was created.**

---

## 13. Decision-by-Decision Classification

**Legend:** `DN` = DECIDE NOW · `DEFER` = DEFER WITH EXPLICIT RATIONALE ·
`FUTURE` = FUTURE PO DECISION · `BLOCKER` = IMPLEMENTATION BLOCKER.
Each entry gives: current state · existing implementation · why it exists · immediate impact ·
classification · recommendation · consequence if deferred · security/data-integrity risk if
deferred · stage affected.

### A1 — Narrative allowlist / editable field set
**Current state:** no editable field; `user_edits JSONB` dormant and unexposed.
**Existing implementation:** 12 system sections in `generated_content.content`; no overlay layer.
**Why it exists:** "bounded allowlist" must be defined before editing ships.
**Immediate impact:** none — S1 has no editing path.
**Classification:** **`DEFER`**.
**Recommendation (not required now):** plain-text allowlist + per-field caps; no HTML/links.
**If deferred:** S2 can add an opaque `narrative_overlay` JSONB column without the key list.
**Risk if deferred:** none, provided no editing endpoint ships before the allowlist exists.
**Stage:** S4.

### A2 — Consultant / staff approval
**Current state:** no report approval mechanism at all; generation requires only `require_org_member()`.
**Existing implementation:** Owner/Admin roles; consultant grants; staff `can_approve` (processing only).
**Why it exists:** undecided whether a consultant/staff member may approve a customer's report.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** no to both (would imply assurance the platform disclaims, §2).
**If deferred:** S1/S2 proceed; S3 must not ship consultant/staff approvers until decided.
**Risk if deferred:** none while no approval endpoint exists; shipping S3 undecided risks an
**assurance misrepresentation** (positioning risk, not a data breach).
**Stage:** S3.

### A3 — Narrative limits
**Current state:** no narrative store, so no limits.
**Existing implementation:** none.
**Why it exists:** unbounded deliverable text is a rendering/abuse concern.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`**.
**Recommendation (not required now):** per-field and per-version caps; plain text only.
**If deferred:** fine, provided the S4 endpoint does not ship without caps.
**Risk if deferred:** none if not built; **DoS/rendering** risk otherwise.
**Stage:** S4.

### A4 — Review gate (mandatory review?)
**Current state:** no review mechanism exists.
**Existing implementation:** none; `REVIEWED` is defined as a lifecycle state.
**Why it exists:** whether `DRAFT → APPROVED` is allowed or `REVIEWED` is mandatory.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** keep `REVIEWED` mandatory, with an optional org policy to auto-review.
**If deferred:** S3 cannot finalise the approval transition matrix.
**Risk if deferred:** none while S3 is unstarted; governance/integrity risk if approval ships undefined.
**Stage:** S3.

### A5 — One-step vs two-step approval
**Current state:** no approval exists.
**Existing implementation:** none.
**Why it exists:** whether review and approval are the same actor/step.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** two-step where the org has >1 authorised actor; single-step acceptable for small orgs.
**If deferred:** S3 blocked on this specific design point.
**Risk if deferred:** none pre-S3.
**Stage:** S3.

### A6 — Approval revocation
**Current state:** no approval exists.
**Existing implementation:** none; the ratified rule is "supersede, never erase".
**Why it exists:** whether/when an approval may be revoked and by whom.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** permit revocation **before** finalization with a recorded reason; never after.
**If deferred:** S3 cannot implement `revoke_approval`.
**Risk if deferred:** none pre-S3; **integrity** risk if revocation were allowed post-finalization
without a decision.
**Stage:** S3.

### A7 — Comment visibility
**Current state:** `report_comments` dormant; no `visibility` column; `comment_type` has no vocabulary.
**Existing implementation:** `report_comments` (report_id, user_id, section_id, comment, comment_type,
is_resolved, resolved_at, resolved_by, resolution_notes).
**Why it exists:** whether internal (staff/consultant) and customer-visible comments coexist.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`**.
**Recommendation (not required now):** add `visibility` (`internal` / `shared`) and a `comment_type`
vocabulary; internal comments never customer-visible.
**If deferred:** S2 can add the columns; the visibility *policy* is needed only when the UI ships.
**Risk if deferred:** none if no comment endpoint ships; **confidentiality** risk if internal notes
were exposed without a visibility rule.
**Stage:** S3/S6.

### A8 — Draft deletion
**Current state:** no version states exist, so no draft concept; no delete path for versions
(`ReportVersionsRepository.delete` exists but is **unused by any API**).
**Existing implementation:** `DELETE FROM public.report_versions WHERE id = $1`.
**Why it exists:** whether a customer may discard a draft.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** permit `DRAFT`-only deletion (preferably soft-discard); never `APPROVED`/`FINAL`.
**If deferred:** no deletion capability ships — the safe default.
**Risk if deferred:** **none** (the safe direction); risk arises only from a *permissive* decision.
**Stage:** S3+.

### A9 — Change-request blocking
**Current state:** no comments, no approval.
**Existing implementation:** none.
**Why it exists:** whether unresolved `change_request` comments must block approval.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** yes — unresolved change requests block approval.
**If deferred:** S3 approval can ship without the block, but then a report may be approved over an
open objection.
**Risk if deferred:** **governance/integrity** (approval over open objections), not a breach.
**Stage:** S3.

### A10 — Retention / deletion
**Current state:** no report lifecycle deletion policy; retention tooling exists
(`backend/services/retention.py`, `backend/tools/enforce_retention.py`); `calculation_snapshots` and
`audit_trail` are append-only.
**Existing implementation:** N3 retention is configurable and server-side through the admin plane.
**Why it exists:** how long report instances/versions/comments/artifacts live, and whether `FINAL`
reports may ever be deleted.
**Immediate impact:** none for S1/S2 (no artifacts, no lifecycle deletion).
**Classification:** **`FUTURE`** (with a legal-review prerequisite).
**Recommendation:** `APPROVED`/`FINAL` never deleted; artifact retention indefinite while the
version exists; drafts subject to policy.
**If deferred:** S1/S2 unaffected; S5 must not make artifacts deletable by default.
**Risk if deferred:** **none** while no artifact exists; **evidence-integrity** risk if artifacts
were made deletable without policy.
**Stage:** S5 / admin policy.

### A11 — Download auditing
**Current state:** **[FACT]** `v3_reports.py` makes **no audit calls at all**.
**Existing implementation:** `audit_trail` + Phase 7 taxonomy with `CAT_REPORT = "report"` and an
action-prefix map that already routes `report*` actions to that category.
**Why it exists:** whether downloading a report/final PDF is an audited event.
**Immediate impact:** **none for S1** (S1 adds no new download path — the existing `/download` and
`/pdf` routes are unchanged).
**Classification:** **`DEFER`** — the S1 docstring correction should **not** silently introduce
auditing; auditing belongs with the lifecycle's audit workstream.
**Recommendation:** audit `report.downloaded` when the lifecycle audit workstream lands (S3/S5).
**If deferred:** no download audit trail.
**Risk if deferred:** **observability** gap only; not a breach.
**Stage:** S3/S5.

### A12 — Staleness / data-as-of
**Current state:** reports snapshot content at generation; no staleness indicator exists.
**Existing implementation:** `generated_content` carries `generation.generated_at` and `lineage`
counts; `calculation_snapshots` carry `calculated_at`.
**Why it exists:** what happens when source carbon data changes after approval.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`**.
**Recommendation (not urgent):** flag stale and display "data snapshot as of"; **never** silently
change an approved report.
**If deferred:** approved reports simply carry no staleness badge.
**Risk if deferred:** none — the ratified rule already forbids silent change; this only affects
*visibility* of staleness.
**Stage:** S6 (UI) / S3 (metadata).

### A13 — Evidence drill-down exposure
**Current state:** **[FACT]** `GET /api/v3/emissions/{log_id}/evidence` exists (org-scoped via
`ensure_org_access`); `domain/evidence.py` classifies COMPLETE/PARTIAL/UNAVAILABLE; frontend
`EvidenceRecordPanel` / `EvidenceTrail` exist.
**Existing implementation:** D33.1 evidence architecture, already exposed to org members.
**Why it exists:** whether the **final report** should expose calculation/evidence drill-down.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`**.
**Recommendation (not required now):** yes, subject to the viewer's authorization — the report is an
evidence-backed presentation, so drill-down is consistent with the ratified model.
**If deferred:** the report links out less; no functional harm.
**Risk if deferred:** none; exposure must remain authorization-checked whenever added.
**Stage:** S6.

### A14 — Billing / entitlement gating
**Current state:** **[FACT]** `usage_tracking.reports_generated` is **only read**
(`services/billing.py:201`), never incremented by the reports surface; `report_generation_queue`
already carries `ai_cost` / `ai_tokens_used` columns for future AI accounting.
**Existing implementation:** `billing_plans`, `billing_credit_ledger`, `billing_commercial_config`,
`usage_tracking`, `v3_billing.py` / `v3_commercial.py`.
**Why it exists:** whether finalization/report generation is entitlement-gated.
**Immediate impact:** none for S1/S2 — no billing behaviour changes.
**Classification:** **`FUTURE`**.
**Recommendation:** do not gate S1/S2; decide commercial policy before any gating.
**If deferred:** reporting remains ungated (current behaviour).
**Risk if deferred:** **commercial** risk only; not security or integrity.
**Stage:** S7 / commercial.

### A15 — Legacy live-render PDF route disposition
**Current state:** **[FACT]** `GET /api/v3/reports/{id}/pdf` renders on demand via
`render_branded_pdf` and is **not stored**; the `download_report` docstring wrongly says no V3 PDF
rendering exists.
**Existing implementation:** `engines/pdf_render.py` + `resolve_report_branding` (server-authorized).
**Why it exists:** after S5 a `FINAL` version must serve the stored artifact, not a fresh render —
so the live-render route's role must be decided.
**Immediate impact:** none for S1/S2 (S1 only corrects the docstring; it does **not** change the route).
**Classification:** **`FUTURE`**.
**Recommendation:** keep live-render for non-final versions; use the stored artifact for `FINAL`.
**If deferred:** S2/S5 proceed; the ambiguity resolves when the frozen model is built.
**Risk if deferred:** **evidence-integrity** risk if a `FINAL` download re-rendered instead of
serving the frozen artifact — but only once S5 exists.
**Stage:** S5.

### A-PE — PE access to customer report documents
**Current state:** **[FACT]** `backend/api/v3_pe.py` (662 lines, 21 routes) has **zero** report
references; PE has no report route, no scope mechanism and no UI for customer reports.
**Existing implementation:** `require_entity_scope` + PE-adjacent `ops/entities/{id}/performance`
and `audit-activity`; PE frontend surfaces (`PEDedicatedHome`, `PEManagerDashboard`).
**Why it exists:** whether the ratified "PE Admin portfolio reporting" surface implies access to
customer report documents.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** **No** — keep PE report-document access = No; PE portfolio reporting is
management reporting over the PE's own authorised entities (§6.2; Blueprint §5.3/§7/§8).
**If deferred:** no PE change; portfolio reporting remains the PE-visible view.
**Risk if deferred:** **none** (the restrictive default); risk arises only from a *permissive*
decision enabling PE to open customer deliverables.
**Stage:** S6 (if ever).

### A-AUD — Auditor assignment / granting model
**Current state:** **[FACT]** no auditor role, table, workspace or API exists (§5.1).
**Existing implementation:** the **consultant active-grant pattern** (`consultant_clients` +
`ensure_consultant_org_access`) is the closest analogue and the recommended shape.
**Why it exists:** a reviewer capability needs an assignment/scoping model (organisation / entity /
report / version) and a grant/revocation mechanism.
**Immediate impact:** none for S1/S2.
**Classification:** **`FUTURE`**.
**Recommendation:** mirror the consultant-grant pattern (explicit grant + ACTIVE/SUSPENDED/ENDED +
revocation) rather than reusing org membership.
**If deferred:** no reviewer access exists — the current, safe state.
**Risk if deferred:** none; risk arises only if reviewer access were granted without scoping.
**Stage:** separate future authorisation.

### A-AUD2 — Reviewer finding record type
**Current state:** `report_comments` is dormant; no finding model exists.
**Existing implementation:** the `issues` domain (defect/exception/escalation; severity; SLA;
lifecycle) is distinct from messaging and QC; `report_comments` has resolution semantics.
**Why it exists:** whether reviewer findings live as comments, as issues, or in a new table.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`** (§12.3).
**Recommendation:** comments + structured metadata first; a dedicated finding model only if
findings need independent lifecycle states, severity SLA or cross-report aggregation.
**If deferred:** no finding capability; nothing breaks.
**Risk if deferred:** none; **duplication** risk if a finding table were added prematurely.
**Stage:** reviewer-capability stage.

### A-LEG — Legacy disposition + future framework report types
**Current state:** **[FACT]** the legacy report monolith and FPDF generator are **not mounted**;
the authoritative catalogue is `annual` only (§8.1).
**Existing implementation:** `backend/routes/reports.py`, `backend/report_generator.py` (dead);
`report_templates` exists but is not used by V3 creation.
**Why it exists:** whether to retire the legacy surface, and whether `SECR`/other frameworks should
become formal V3 report types.
**Immediate impact:** **none for S1.**
**Classification:** **`DEFER`** (disposition) + **`FUTURE`** (future framework types).
**Recommendation:** leave legacy code untouched (AGENTS.md §79); keep legacy labels out of the live
product; treat any future framework report as a **separate PO-authorised product decision** with its
own specification.
**If deferred:** no change; legacy remains unreferenced.
**Risk if deferred:** none; risk arises only from an unmanaged revival or deletion.
**Stage:** separate.

### A-RLS — Report-table RLS approach
**Current state:** **[FACT/CORRECTED]** RLS **is enabled** on all four report tables (schema-wide
enablement loop, `init_schema.sql:2315-2324`), but **policy coverage is incomplete**:
`report_generation_queue` and `report_templates` carry `organization_id` and receive tenant policies
from `rc2_rls.sql` §3; `report_versions` and `report_comments` have **no `organization_id` and
therefore no policy** (deny-all to `authenticated` under RLS). Backend access works because the
connection role bypasses RLS (not `FORCE`d) — the posture Blueprint §14 records as an open hardening
item. **Effective control today = API-layer guards** (§4).
**Existing implementation:** `is_org_member` / `is_org_consultant` helpers; dynamic tenant policy
generator; negative org-isolation tests in `test_v3_reports.py`.
**Why it exists:** a security-architecture choice with migration implications: complete policy
coverage vs a documented app-layer-only posture.
**Immediate impact:** **none for S1** — S1 changes no table, column, policy or endpoint.
**Classification:** **`FUTURE`** for the decision; **`BLOCKER` for S2** (not for S1).
**Recommendation:** **(a)** complete the policy coverage for `report_versions`/`report_comments`
using the existing `organization_id` + `is_org_member` pattern (preferred); or **(b)** formally
document the app-layer-only posture. Either way: **weaken nothing**.
**If deferred:** S1 proceeds safely; S2/S3 must not add lifecycle writes before deciding.
**Risk if deferred:** **medium** — the split posture is *accidental*, and a future maintainer could
mistake `report_versions` for RLS-protected. **No live breach is demonstrated** (API guards + owner
bypass), so this is a **defence-in-depth and documentation** risk, not a proven exposure.
**Stage:** S2.

### A-ROAD — Master Roadmap update
**Current state:** **[FACT]** roadmap §0/§11/§13/§14/§18 contain stale phase status (§9.1).
**Existing implementation:** n/a (documentation).
**Why it exists:** the roadmap still says Phase 8 is "NOT AUTHORIZED" and Phase 6 is current.
**Immediate impact:** **none** — no implementation depends on the roadmap text.
**Classification:** **`FUTURE`** (documentation governance).
**Recommendation:** apply the six bounded updates listed in §9.3 at a documentation checkpoint.
**If deferred:** the roadmap remains internally stale but does not misdirect S1/S2.
**Risk if deferred:** **none** technically; **governance** drift risk.
**Stage:** documentation.

### A-ASSUR — Assurance-readiness scoring
**Current state:** **[FACT]** an evidence-based readiness indicator exists (labelled "AUDIT
EVIDENCE READINESS", `not_assurance: true`); **no numeric score exists** and no methodology for one.
**Existing implementation:** `audit_readiness_from_counts(...)`, `AUDIT_NOT_ASSURANCE_NOTICE`.
**Why it exists:** whether a score is a product feature.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`** (§10.3).
**Recommendation:** do not build a score; the readiness indicator is the safe framing. Revisit only
with a published methodology, careful labelling, and legal review.
**If deferred:** no score; nothing breaks.
**Risk if deferred:** none; **positioning/legal** risk arises only from introducing a score.
**Stage:** separate.

### A-STAFF — Staff capability model
**Current state:** **[FACT]** capability flags exist
(`can_approve, can_review, can_view_all, can_manage_staff`, …) seeded per role; `can_approve`
concerns **processing** approval today.
**Existing implementation:** `staff_roles.permissions` JSONB + `backend/domain/staff.py` +
`backend/routes/admin/permissions.py`.
**Why it exists:** whether report review/approval needs staff capabilities.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`** (§11.3).
**Recommendation:** customer-only for the current lifecycle implementation; revisit at S3+ only if
the PO permits staff action (`A2` governs).
**If deferred:** no staff report capability; nothing breaks.
**Risk if deferred:** none; **assurance-misrepresentation** risk if staff approval were added without
a PO decision.
**Stage:** S3+.

### A-COMMENT — Comment visibility granularity
**Current state:** `report_comments` dormant; no `visibility` column; `comment_type` has no vocabulary.
**Existing implementation:** see §12.1.
**Why it exists:** whether visibility is per-comment or per-thread.
**Immediate impact:** none for S1/S2.
**Classification:** **`DEFER`** (§12.3).
**Recommendation (not required now):** per-comment `visibility` (`internal` / `shared`) is simpler
and sufficient initially; per-thread only if threading is later introduced.
**If deferred:** S2 can add the column; the granularity choice affects only the S3/S6 UI.
**Risk if deferred:** none; **confidentiality** risk only if internal notes were exposed without a
visibility rule.
**Stage:** S3/S6.

---

## 14. Final Implementation-Authorisation Matrix

| Item | Classification | Decide Now? | Blocks S1? | Blocks later lifecycle? | Recommended action |
|---|---|:-:|:-:|:-:|---|
| **A1** narrative allowlist | `DEFER` | No | **No** | Yes (S4) | Decide before S4; add opaque `narrative_overlay` column in S2 |
| **A2** consultant/staff approval | `FUTURE` | No | **No** | Yes (S3) | Decide before S3; recommend **no** |
| **A3** narrative limits | `DEFER` | No | **No** | Yes (S4) | Decide with A1 |
| **A4** review gate | `FUTURE` | No | **No** | Yes (S3) | Decide before S3; recommend `REVIEWED` mandatory |
| **A5** one-step vs two-step | `FUTURE` | No | **No** | Yes (S3) | Decide before S3 |
| **A6** approval revocation | `FUTURE` | No | **No** | Yes (S3) | Decide before S3; revoke pre-finalization only |
| **A7** comment visibility | `DEFER` | No | **No** | Yes (S3/S6) | Add `visibility` in S2; policy before UI |
| **A8** draft deletion | `FUTURE` | No | **No** | No (absence is safe) | Decide before S3+; recommend DRAFT-only |
| **A9** change-request blocking | `FUTURE` | No | **No** | Yes (S3) | Decide before S3; recommend blocking |
| **A10** retention/deletion | `FUTURE` | No | **No** | Yes (S5) | Decide with legal review before S5 |
| **A11** download auditing | `DEFER` | No | **No** | Yes (S3/S5) | Emit `report.downloaded` in the lifecycle audit workstream |
| **A12** staleness / data-as-of | `DEFER` | No | **No** | No (visibility only) | Add at S6; never auto-mutate an approved report |
| **A13** evidence drill-down | `DEFER` | No | **No** | Yes (S6) | Decide before S6; authorization-checked |
| **A14** billing/entitlement gating | `FUTURE` | No | **No** | No | Decide before any gating |
| **A15** legacy live-PDF route | `FUTURE` | No | **No** | Yes (S5) | Decide before S5 |
| **A-PE** PE access to customer reports | `FUTURE` | No | **No** | No | Confirm **No**; portfolio reporting is separate |
| **A-AUD** auditor granting model | `FUTURE` | No | **No** | No (separate capability) | Decide at reviewer-capability stage |
| **A-AUD2** finding record type | `DEFER` | No | **No** | No | Comments + metadata first |
| **A-LEG** legacy disposition | `DEFER` / `FUTURE` | No | **No** | No | Leave untouched; no revival |
| **A-RLS** report-table RLS approach | `FUTURE` (decision) / `BLOCKER` (for S2) | **No** | **No** | **Yes (S2)** | Decide before S2; complete coverage or document app-layer-only |
| **A-ROAD** roadmap update | `FUTURE` | No | **No** | No | Update at a docs checkpoint |
| **A-ASSUR** readiness scoring | `DEFER` | No | **No** | No | Do not build a score |
| **A-STAFF** staff capability model | `DEFER` | No | **No** | No | Customer-only for now |
| **A-COMMENT** visibility granularity | `DEFER` | No | **No** | Yes (S3/S6) | Per-comment `visibility` initially |
| **RLS CORRECTION** (§4) | Correction | **Acknowledge** | **No** | No | Record the correction; no S1 impact |

### 14.1 Matrix summary

* **Decide now:** **none.**
* **Block S1:** **none.**
* **Block later lifecycle:** A1, A2, A3, A4, A5, A6, A7, A9, A10, A11, A13, A15, **A-RLS (S2)**,
  A-COMMENT.
* **Security/data-integrity risk if deferred:** **A-RLS** (medium — defence-in-depth/documentation);
  A10/A15 (integrity, only once S5 exists); A9/A2 (governance/positioning); all others **none**.

---

## 15. S1 Authorisation Status

### READY FOR PO AUTHORISATION

**Basis:**

* **No unresolved blocker remains for S1.** Every open decision is classified `DEFER` or `FUTURE`;
  none is `DECIDE NOW`, and none blocks S1 (§13, §14).
* **S1 scope is sufficiently defined** (§7.3): fix the `is_current` invariant (repository-level,
  **no migration**), expose `current_version` in the report listing (single query, no N+1), and
  correct the stale `download_report` documentation.
* **S1 introduces no schema, RLS, API-contract, lifecycle, frontend, PDF or AI surface** (§7.4), so it
  cannot pre-empt any PO decision.
* **S1 is required for correctness** before the S2 schema stage (the ratified sequencing principle).

**Conditions attached to this status (advisory, not blockers):**

1. The **§4 RLS correction** should be acknowledged, and the three prior documents annotated at their
   next revision. This does **not** block S1 — S1 touches no RLS artefact.
2. The **`is_current` fix should be delivered in the S1-A (repository-level) shape**, with the
   structural S1-B variant deferred to the S2 schema stage (§7.3).
3. A regression test for the single-current-version invariant — and continued passage of the existing
   `test_v3_reports.py` suite — should form part of S1's acceptance evidence.

**No implementation should start until the PO explicitly authorises S1.** This document does **not**
authorise it, and no S1 code, migration or test has been written.

---

## 16. Final PO Decision Package

### A. Decisions the PO must make before S1

**NONE.**

No genuine blocker exists for S1. Two items require PO **awareness/confirmation** rather than a
decision:

| Item | Nature | Why it is not a blocker |
|---|---|---|
| §4 RLS correction | Acknowledgement that the prior "no RLS on report tables" statements were inaccurate | S1 changes no RLS artefact; the correction affects **S2** planning, not S1 scope |
| S1-A vs S1-B fix shape | Scope confirmation (repository-level fix, no migration) | S1-A is **within** the declared S1 boundary; S1-B would be a scope *expansion* needing separate authorisation |

**Minimum to proceed:** the PO authorises **S1 as scoped in §7.3** (S1-A).

### B. Decisions the PO can safely defer

| Item | Rationale for safe deferral |
|---|---|
| **A1 / A3** narrative allowlist + limits | S2 can add an opaque `narrative_overlay` JSONB column without the key list; validation belongs to S4 |
| **A7 / A-COMMENT** comment visibility (+ granularity) | S2 can add columns; the visibility *policy* is needed only when a comment surface ships |
| **A8** draft deletion | Absence of deletion is the **safe** default |
| **A11** download auditing | S1 adds no download path; the audit workstream attaches to the lifecycle stages |
| **A12** staleness / data-as-of | Affects *visibility* only; the ratified rule already forbids silent change |
| **A13** evidence drill-down | Decision needed at S6, not before |
| **A-AUD2** finding record type | Comments + metadata suffice initially; no duplication should be created |
| **A-LEG** legacy disposition | Legacy is unmounted and unreferenced; leaving it untouched is safe (AGENTS.md §79) |
| **A-ASSUR** readiness scoring | No score exists; the readiness indicator is already the safe framing |
| **A-STAFF** staff capability model | Customer-only is the ratified default; no staff capability needed |
| **A-ROAD** roadmap update | Documentation-only; no implementation depends on it |
| **A-PE** PE report-document access | The current restrictive default is safe; portfolio reporting covers PE needs |
| **A14** billing/entitlement gating | No gating exists; commercial policy can follow |

### C. Decisions that belong to later Phase 8 stages

| Item | Stage | Prerequisite |
|---|---|---|
| **A-RLS** report-table RLS approach | **S2** | Security-architecture decision: complete policy coverage vs documented app-layer-only posture. **Blocks S2, not S1** |
| **A2 / A4 / A5 / A6 / A9** approval & review design | **S3** | PO decision on approvers, review gate, steps, revocation, change-request blocking |
| **A1 / A3** narrative model | **S4** | PO decision on the allowlist and limits |
| **A15** live-PDF route disposition | **S5** | PO decision on draft live-render vs frozen-artifact route |
| **A10** retention/deletion | **S5** | PO decision **+ legal review** |
| **A12 / A13** staleness & drill-down | **S6** | Decisions on visibility and drill-down exposure |
| **A-PE** PE access | **S6** (if ever) | PO confirmation of the architectural "No" |
| **A-AUD / A-AUD2** reviewer capability | **Separate** | Its own scoped trust model + authorisation |
| **A-ASSUR / A-STAFF / A-LEG / A-ROAD / A14** | **Separate / documentation / commercial** | As listed above |

### D. Recommended Next Implementation Sequence

```text
S0 — PO closure
       Ratify this package: acknowledge the §4 RLS correction; confirm no S1 blockers;
       authorise S1 as scoped (S1-A: repository-level is_current fix, no migration).

S1 — Report correctness foundation            [requires explicit S1 authorisation]
       • fix the report_versions.is_current invariant (repository-level, single transaction)
       • expose current_version in the report listing (one query, no N+1)
       • correct the stale download_report documentation
       • regression test: exactly one is_current = TRUE per report after two versions
       • existing test_v3_reports.py suite continues to pass

↓  INDEPENDENT VERIFICATION of S1 (separate; not self-certified)

S2 — Lifecycle schema + RLS decision         [requires separate authorisation]
       • decide A-RLS; add version state + narrative_overlay + comment additions
       • consider the S1-B partial unique index (with the live duplicate check)

↓  S3 … S8 only after explicit PO authorisation for each stage
```

**S2 and beyond are NOT authorised by this package.** No stage may begin without its own explicit PO
authorisation (§7.4, §14.1).

---

## 17. Verification and Non-Implementation Boundary

### 17.1 Verification performed

| # | Check | Result |
|---|---|---|
| 1 | Both required documents exist | ✅ |
| 2 | Internally consistent (S1 boundary matches §7.3, §14, §15; classifications match §13 and §14) | ✅ |
| 3 | Every open decision classified (A1–A15, A-PE, A-AUD, A-AUD2, A-LEG, A-RLS, A-ROAD, A-ASSUR, A-STAFF, A-COMMENT) | ✅ |
| 4 | S1 boundary explicit | ✅ (§7.3, §7.4, §14, §15) |
| 5 | No implementation performed | ✅ |
| 6 | No database/schema/RLS/API/frontend/production changes | ✅ |
| 7 | No unrelated dirty/untracked work removed or modified | ✅ (counts unchanged) |

### 17.2 What this task did NOT do

```text
Code changes:            NONE
Database changes:        NONE
Migrations:              NONE
RLS changes:             NONE
API changes:             NONE
Frontend changes:        NONE
Report-engine changes:   NONE
PDF changes:             NONE
AI / LLM changes:        NONE
Billing changes:         NONE
Messaging changes:       NONE
Production changes:      NONE
Roadmap edits:           NONE
Legacy code changes:     NONE
Authorization changes:   NONE
Push to remote:          NONE
```

### 17.3 Files intentionally untouched

`supabase/migrations/**`, `supabase/config.toml`, `backend/**`, `frontend/**`, `database/**`,
`AGENTS.md`, `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`,
`CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`, the three prior Phase 8 documents (corrections
**recorded here**, not applied), and all legacy report code.

### 17.4 Stop-condition compliance

**No stop condition was triggered.** Specifically:

* no implementation was required to answer any decision;
* no production access was used;
* no migration was executed;
* **live RLS testing was not performed** — the resulting unknowns are marked `[UNVERIFIED]` (§4.5),
  and the recommendation is stated so that it does not depend on them;
* no decision was resolved by guesswork; items not answerable from the repository are marked
  **PO DECISION**.

### 17.5 The distinction that governs this package

| Category | Examples here |
|---|---|
| **Repository fact** | RLS enabled but unpolicied on two report tables; no auditor role; PE has no report route; `is_current` defect; stale docstring; roadmap drift |
| **Architectural recommendation** | S1-A fix shape; complete RLS coverage; consultant-grant pattern for reviewers; comments before findings; no readiness score |
| **PO decision** | A-RLS approach; approval roles/steps; narrative allowlist; retention; PE access confirmation |
| **Future work** | All of S2–S8; reviewer capability; readiness scoring; legacy disposition |

```text
PHASE 8 OPEN-DECISION CLOSURE COMPLETE
STATUS:                   DECISION PACKAGE / DOCUMENTATION ONLY
IMPLEMENTATION AUTHORISED: NONE (S1 included)
DECISIONS CLASSIFIED:     24/24 (+ 1 correction)
DECIDE NOW:               NONE
S1 BLOCKERS:              NONE
S1 AUTHORISATION STATUS:  READY FOR PO AUTHORISATION
MATERIAL CORRECTION:      report-table RLS statement corrected (§4)
BLOCKS S2:                A-RLS (report-table RLS approach)
CODE / DB / RLS / API / FE / PROD:  NONE
MIGRATIONS:               NONE
LLM / PROVIDER / KEY:     NONE
PUSH:                     NONE
```

*End of decision package.*
