# CarbonTally V3 — MASTER WORKFLOW MAP

| | |
|---|---|
| Document type | Workflow map (authoritative) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | AUTHORITATIVE (UX phase) — reconciled with backend state model |
| Date | 2026-08-24 |

## 1. Backend state model (authoritative vocabularies)

Source: `backend/domain/partners.py`, `backend/domain/entity.py`,
`backend/domain/issue.py`, `backend/api/v3_reports.py`.

- **ITEM_STATUSES** (manual-extraction items):
  `pending, extracting, extracted, mapping, mapped, validating, validated,
  calculating, calculated, customer_review, approved, rejected, qc_approved,
  qc_rejected, failed`
- **BATCH_STATUSES** (manual-extraction batches):
  `open, in_progress, qc_in_progress, qc_passed, completed, cancelled, failed`
- **WORKFLOW_STAGES**: `source, extraction, mapping, validation, calculation,
  review, approval` (+ orthogonal `qc`)
- **ENTITY_STATUSES** (Processing Entities):
  `active, remediation, suspended, terminated`
- **ISSUE_STATUSES**: `open, in_progress, on_hold, escalated, resolved, closed`
- **REPORT_STATUSES**: `pending, generating, completed, failed`
- **ITEM_STATUS_FLOW** (allowed transitions) is the workflow state machine;
  validation failures and customer rejections route items back to
  mapping/extracting (rework loop) rather than introducing new statuses.

## 2. Core workflow (canonical pipeline)

```
UPLOAD ──> CLASSIFY ──> EXTRACT ──> MAP ──> VALIDATE ──> PE REVIEW/QC ──> CARBONTALLY QC
  │          │           │          │         │            │                │
  │          │           │          │         │            │                │
  ▼          ▼           ▼          ▼         ▼            ▼                ▼
CALCULATE ──> EVIDENCE ──> CUSTOMER REVIEW ──> CUSTOMER APPROVAL ──> REPORTING
```

### 2.1 Stage-by-stage (roles, states, surfaces)

| # | Stage | Item status(es) | Roles | Surface | Notes |
|---|---|---|---|---|---|
| 1 | Upload | batch `open` | O/A/M/V (create); C conditional | Documents / Processing | `organization_files` + `upload_batches`; D32 private storage. |
| 2 | Classification | `pending` → `extracting` | engine + staff | Processing | Document classifier (`backend/utils/document_classifier.py`). |
| 3 | Extraction | `extracting` → `extracted` | S operator; E (assigned) | Workbench (D19) | `v3_processing_workflow` start/extract; AI suggestion (D16). |
| 4 | Mapping | `mapping` → `mapped` | S operator; E | Workbench | Factor candidates; server-authoritative selection (D9/D16). |
| 5 | Validation | `validating` → `validated` | S reviewer | Workbench | ValidationEngine A1–A9; failures → rework. |
| 6 | PE review/QC (if entity-assigned) | `qc_approved`/`qc_rejected` | E | Entity workspace | Entity staff QC their assigned work; CarbonTally mediates. |
| 7 | CarbonTally QC | `qc_approved`/`qc_rejected` | S (can_review); admin QC surface | QC queue | Internal QC gate. |
| 8 | Calculation | `calculating` → `calculated` | S/E | Workbench | Server-authoritative calculation engine; snapshot (immutable). |
| 9 | Evidence | `calculated` (with evidence record) | all (read) | Evidence panel (D33) | Complete/Partial/Unavailable. |
| 10 | Customer review | `customer_review` | O/A/M/V (review) | Customer review UI (target) | Evidence-first review. |
| 11 | Customer approval | `approved` / `rejected` | O/A (approver authority, D5) | Approve/Reject UI (target) | Distinct responsibility; audit + reason. |
| 12 | Reporting | report `pending→generating→completed/failed` | O/A/M/V; C | Reports | `v3_reports`; branding context (D21). |

### 2.2 Rework / rejection loops

- Validation failure → item returns to `mapping` (or `extracting`).
- Customer rejection → item returns to `mapping`/`extracting` with a reason
  (recorded; issue may be raised).
- QC rejection (`qc_rejected`) → item returns to extraction/mapping with QC
  notes.
- These loops are state-machine-safe (`ITEM_STATUS_FLOW`), not new statuses.

## 3. Assignment workflow (D22)

```
CarbonTally staff (can_manage_staff + can_process) assigns a batch
   └─ exactly ONE active party: internal operator (assigned_to) XOR
      Processing Entity (entity_id)
        └─ entity staff process ONLY their entity's assigned batches
        └─ internal operators never see entity-assigned batches
        └─ reassignment records before→after in audit_trail (ADR-V3-013)
```

## 4. Clarification workflow (mediated)

```
Entity staff ──> entity-scoped Issue ──> CarbonTally ──> Customer
                    (never direct; D6/D18 + N1-E boundary)
```

**N1 (messaging access) governs who may converse with whom.** There is no
direct Customer ↔ Processing Entity messaging: processing clarification is
the controlled workflow above. Customer/consultant/support messaging follows
the N1 model (org-scoped; consultant active-client scope; Customer Support /
Admin scoped support threads; PE Manager↔PE users; PE↔CarbonTally
operational). Enforcement is RLS/API (N1-F); the UI is not the boundary.

## 5. Issue workflow

`open → in_progress → on_hold → escalated → resolved → closed`

Issue types are first-class (ADR-V3-009); conversations may be associated but
remain separate concepts. Customer sees org issues (entity issues excluded);
staff see ops-wide; entity staff see their entity's issues.

## 6. Invitation / membership workflow (D10)

```
Invite (org admin) ──> pending_invites ──> Accept ──> organization_members
   (role owner/admin/member/viewer) ──> active membership
No dead end: a relationship-less user lands on /onboarding (D35).
```

## 7. Onboarding workflow (D35)

```
/signup (self-service) ──> Supabase Auth ──> /onboarding
   ├─ create organisation (POST /api/v3/organizations) ──> creator = OWNER
   └─ existing-data discovery (lookup → request → verify → USE ALL/PARTIAL/DISCARD)
   └─ proceed (guided first steps)
```

## 8. Billing workflow (D37)

```
Subscription lifecycle: pending/trial/active/past_due/suspended/cancelled/expired
Billing modes: CREDIT (complexity bands) | STANDARD (monthly allowance)
Orders: draft → estimated → awaiting_customer_approval → approved → queued →
        processing → awaiting_qc → completed | cancelled/rejected/failed/refunded
Credit ledger: grant/consume/rollover/emergency/adjustment/reversal/refund (append-only)
No live payment provider (provider-neutral; adapters future).
```

## 9. Custom factor workflow (D9)

```
DRAFT (staff/member creates) ──> REVIEW (org Admin/Owner approves; no self-approval)
   ──> ACTIVE ──> ARCHIVED/INACTIVE (soft-deactivate)
Precedence: approved customer factor → CarbonTally factor → unresolved/manual review
Snapshot provenance: factor_source='CUSTOMER' (O1 exactly-one-source)
```

## 10. Processing Entity lifecycle

`active → remediation → suspended → terminated`; only `active` grants entity
access. Suspension/termination never deletes history; assigned work needs a
defined disposition.

## 11. AI assistance (D16)

AI MAY assist navigation, explanations, document assistance, extraction
suggestions, workflow guidance, contextual help. AI MUST NOT be authoritative
for calculations, factor selection, evidence, approval, security, org
boundaries or compliance certification. AI extraction suggestions carry
confidence and require human confirmation before becoming data.

## 12. Master-data workflows (D17)

Master-data entities (Facilities, Locations, Assets, Vehicles, Suppliers) are
organisation-scoped and secondary to the processing pipeline (D18). The D17
lifecycle applies to each:

```
CREATE → CONFIGURE → USE → EDIT → ARCHIVE/DEACTIVATE → RESTORE (where supported)
          └─────────── view related activity / documents / emissions / evidence
```

| Entity | Current capability (implementation evidence) | Where it hooks into workflows |
|---|---|---|
| Facilities | IMPLEMENTED — `facilities` table (doubles as locations), org-scoped API + admin tab | Source documents/activity attach; emissions/evidence link |
| Locations | NOT a separate table today (facilities serves as "facilities/locations") — **N2 resolved**: dedicated Locations table OR Facilities reuse is an engineering decision against the existing schema | Target: hierarchy above Facilities |
| Assets | IMPLEMENTED — `assets` table, org-scoped API + admin tab | Related documents/activity/emissions |
| Vehicles | **NOT IMPLEMENTED** (no table/API/UI) — gap G-P1-2 | Target: org-scoped master data |
| Suppliers | IMPLEMENTED — `suppliers` table, org-scoped API + admin tab | Extraction mapping candidates; activity/evidence |

Master data never blocks normal processing: users are not forced to configure
every entity before uploading or processing (D17).

*End of workflow map. Documentation-only.*
