# CarbonTally V3 — FAQ Capability & Evidence Matrix

**Internal document.** This matrix backs every claim in
`CARBONTALLY_V3_CUSTOMER_FAQ.md` and in the public website FAQ
(`website_candidate/frontend/src/public/faqData.js`, rendered at `/faq`).
It is not customer-facing.

Any FAQ claim that cannot be traced to a row in this matrix must be removed or
qualified before publication.

**Public website note.** The website FAQ presents the complete intended
CarbonTally service (target state) and intentionally does not expose
implementation status. Rows marked `C — BACKEND-ONLY` (for example customer
approval, custom factors UI, PDF download) are the implementation gaps Cline
must close to match the public presentation; they are implemented server-side
but their customer UI is incomplete. They are not gaps in the approved
product/service model.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| VERIFIED | Confirmed in code, schema, RLS or authoritative documentation |
| IMPLEMENTED | Present and usable in the current product |
| BACKEND-ONLY | Backend/API capability exists; customer UI missing or incomplete |
| SERVICE | Human-assisted service CarbonTally explicitly intends to provide (PO decision register) |
| PROPOSED | Proposed in this or an audit/blueprint document; not yet decided/built |
| FUTURE / PLANNED | Explicitly identified as future |
| PO DECISION REQUIRED | Detail depends on an unresolved Product Owner decision |
| NOT ESTABLISHED | No supporting evidence; must not be claimed |

**Capability classification (per FAQ task)**

- **A — CURRENT PRODUCT CAPABILITY**: confirmed by implementation/docs.
- **B — CURRENT HUMAN-ASSISTED SERVICE**: service CarbonTally explicitly
  intends to provide via staff or Processing Entities.
- **C — ESTABLISHED CAPABILITY, UI/WORKFLOW INCOMPLETE**: backend exists,
  customer UI incomplete.
- **D — PLANNED / FUTURE**.
- **E — NOT CURRENTLY OFFERED / NOT ESTABLISHED**.

---

## 2. Evidence index (key sources)

- PO register: `docs/ChatGPT/CARBONTALLY_V3_PRODUCT_OWNER_DECISION_REGISTER_v1.md`
- UI/UX audit: `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_PLATFORM_UI_UX_AUDIT.md`
- UX blueprint: `docs/audit/openhands/CARBONTALLY_V3_AUTHENTICATED_UX_BLUEPRINT.md`
- Extraction/mapping/calculation audit: `docs/audit/openhands/extraction-mapping-calculation/CARBONTALLY_V3_EXTRACTION_MAPPING_CALCULATION_CAPABILITY_AUDIT.md`
- Regulatory audit: `docs/audit/openhands/CARBONTALLY_V3_INDEPENDENT_REGULATORY_AND_DATA_RESIDENCY_AUDIT.md`
- PE security audit: `docs/audit/openhands/CARBONTALLY_V3_PE_SECURITY_AUDIT.md`
- Backend: `backend/api/v3_uploads` (in `v3_documents.py`), `v3_documents.py`,
  `v3_manual_extraction.py`, `v3_processing_workflow.py`, `v3_emissions.py`,
  `v3_reports.py`, `v3_exports.py`, `v3_issues.py`, `v3_messaging.py`,
  `v3_billing.py`, `customer_factors.py`, `v3_consultants.py`,
  `v3_operations.py`, `consultant_auth.py`, `operations_auth.py`
- Frontend: `frontend/src/App.js`, `frontend/src/v3/**`
- RLS/storage: `supabase/migrations/20260823000000_d32_private_documents_storage.sql`, `20260803000000_rc2_rls.sql`

---

## 3. Internal evidence matrix

| FAQ Topic | Claim | Evidence | Status | Current UI | Backend | Customer Service | PO Decision Required |
|---|---|---|---|---|---|---|---|
| About — what CarbonTally is | UK-based emissions data-processing platform | PO §1.1, §10.4; platform audits | VERIFIED / IMPLEMENTED | yes | yes | yes | no |
| About — processing chain | Source→extract→map→calc→validate→review/QC→approval→evidence→report | PO §5.3, §12; extraction audit | VERIFIED (model) | partial | yes | yes | no |
| About — problem solved | Turns messy documents into traceable validated results | PO §10.4 positioning; audits | VERIFIED (service model) | yes | yes | yes | no |
| About — who for | UK/EU businesses; SME/sustainability/finance/ops/procurement | PO §1.1; marketing docs | VERIFIED (target) | — | — | — | no |
| About — human-assisted processing | CarbonTally staff / approved partners process documents via portal | PO §2.3, §3.3; extraction audit (production path is human-assisted) | VERIFIED / SERVICE | partial | yes | yes | no |
| About — messy data | Handled via human-assisted extraction + mapping + validation | extraction audit; PO §5.3 | VERIFIED / SERVICE | partial | yes | yes | no |
| Documents — supported types | PDF, images (JPG/PNG/GIF/WebP), CSV, XLS, XLSX | `v3_documents.py _classify` (pdf; jpg/jpeg/png/gif/webp; csv/xlsx/xls) | VERIFIED / IMPLEMENTED | upload widget | yes | — | no |
| Documents — scanned PDFs | Uploadable; human-assisted workflow; OCR not in customer workflow | extraction audit (no OCR in production path); `_classify` accepts pdf | VERIFIED (upload) + PLANNED (OCR) | yes (upload) | yes | yes | no |
| Documents — images | Uploadable; human-assisted; automated image reading planned | `_classify` image types; extraction audit (JPG OCR broken/legacy) | VERIFIED (upload) + PLANNED | yes | yes | yes | no |
| Documents — invoices/utility | Typical source documents; extracted by team | generic document model; `document_type` classification | VERIFIED / SERVICE | yes | yes | yes | no |
| Documents — spreadsheets | CSV/Excel uploadable; mapping is a CarbonTally capability; self-service mapping UI incomplete | PO §5.1 (capability); extraction audit (production path treats spreadsheets as manual-extraction items; legacy BulkUpload dead) | C — BACKEND-ONLY for self-service; VERIFIED for upload | upload only | yes (manual items) | yes | no |
| Documents — after upload | Stored privately, classified, enqueued as manual-extraction item | `v3_documents.py` upload → `manual_extraction_item` (D23); D32 private bucket | VERIFIED / IMPLEMENTED | status shown | yes | — | no |
| Documents — extraction fails | Item flagged; customer can raise issue / re-upload | `issues.py` customer issues; item status model | VERIFIED | issues page | yes | — | no |
| Documents — correct extracted info | Via issues + customer review/reject | `v3_processing_workflow.py` customer-review (reject→mapping); issues | VERIFIED (backend) / C (UI) | issues; approval UI pending | yes | — | no |
| Documents — historical | Past bills/invoices uploadable; bulk historical import not offered | no import capability in code | VERIFIED (upload) / NOT ESTABLISHED (import) | yes | — | — | no |
| Extraction/OCR — what OCR is | Plain-language definition | — | n/a | — | — | — | no |
| Extraction/OCR — automated OCR | Not in customer workflow; planned (PO §5.2 recover historical) | extraction audit §1, §3 (no OCR in production HTTP workflow; JPG broken; not persisted); PO §5.2 | D — PLANNED | no | legacy only | planned | no |
| Extraction/OCR — poor quality | Human-assisted; clarification/flag | PO §5.3; entity clarification endpoint | VERIFIED / SERVICE | partial | yes | yes | no |
| Extraction/OCR — correction | Via review/approval + issues | see correction row | VERIFIED (backend) | partial | yes | — | no |
| Extraction/OCR — source of extracted info | Evidence record shows source doc + page | `v3_emissions.py` evidence endpoint (D33/D33.1); `EvidenceRecordPanel` | VERIFIED / IMPLEMENTED | evidence panel | yes | — | no |
| Mapping — what it means | Linking data to activity/facility/unit | `v3_processing_workflow.py` map payload (activity, facility, asset, supplier, unit) | VERIFIED | internal workspace | yes | — | no |
| Mapping — customer self-service | Currently performed by processing team; self-service UI incomplete | extraction audit; blueprint §5.3 | C — BACKEND-ONLY / SERVICE | no | yes | yes | customer processing role |
| Mapping — messy data | CarbonTally helps map | SERVICE (PO §2.3 mapping by PE/CT) | VERIFIED / SERVICE | — | yes | yes | no |
| Mapping — cannot identify | Flag + clarification | `validate_processing_item` blocking findings; issues | VERIFIED | issues | yes | — | no |
| Mapping — review/correct | Part of validation/review | validation findings → rework | VERIFIED | internal | yes | — | no |
| Factors — what a factor is | Plain-language definition | — | n/a | — | — | — | no |
| Factors — which sets | DEFRA, SEAI, customer custom; not all countries | PO §6.1; `emission_factors` seeded (PO-verified 7,049 rows); factor provenance fields | VERIFIED | pickers/results | yes | — | no |
| Factors — DEFRA | Supported | PO §6.1; factor data | VERIFIED | yes | yes | — | no |
| Factors — SEAI/Irish | Supported | PO §6.1 | VERIFIED | yes | yes | — | no |
| Factors — custom factors | Established capability; customer management UI being completed | PO §6.2; `customer_factors.py` (list/get/create/update/approve/deactivate) | C — BACKEND-ONLY | none | yes | — | factor editors |
| Factors — selection | Context-based matching (activity, unit, country, year); custom precedence | `engines/factor_matching.py`; customer_factors precedence; PO §6.3 | VERIFIED / IMPLEMENTED | auto-match display | yes | — | no |
| Factors — which factor used | Shown in result + evidence | snapshot factor_id/factor_source; evidence record | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| Factors — source/year | Provenance recorded | snapshot provenance (source/set, reporting year) | VERIFIED / IMPLEMENTED | partial (raw text) | yes | — | no |
| Factors — none found | Item flagged; custom factor option | mapping requires factor (`map_item` 422); custom factors | VERIFIED | — | yes | — | no |
| Factors — traceable | Factor recorded per calculation | snapshot + evidence chain | VERIFIED / IMPLEMENTED | evidence | yes | — | no |
| Calculations — how | quantity × factor, server-authoritative | `engines/calculation.py`; `v3_emissions.py` (client never supplies result); `v3_processing_workflow.py` calculate | VERIFIED / IMPLEMENTED | calculator | yes | — | no |
| Calculations — change result | Cannot change; correct inputs and recalculate | server-authoritative; immutable snapshots (PO §7.3) | VERIFIED | no edit | yes | — | no |
| Calculations — see method | Evidence record shows inputs+method | D33 evidence record; snapshot | VERIFIED / IMPLEMENTED | evidence panel | yes | — | no |
| Calculations — factor shown | Yes | evidence record | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| Calculations — traceable | Item↔snapshot↔result links | D33 source_item_id chain | VERIFIED / IMPLEMENTED | partial | yes | — | no |
| Calculations — data changes | Recalculate; history retained | immutable snapshots + emissions_logs rows | VERIFIED | history list | yes | — | no |
| Validation/QC — validation | Checks completeness/consistency | `validate_processing_item`; findings→issues→rework | VERIFIED / IMPLEMENTED (internal) | internal | yes | — | no |
| Validation/QC — review | Human review of item+evidence | review queue (`can_review`) | VERIFIED / IMPLEMENTED (internal) | internal | yes | — | no |
| Validation/QC — QC | Quality score, notes, pass/fail | `/api/v3/ops/items/{id}/qc`; QcQueue | VERIFIED / IMPLEMENTED (internal) | internal | yes | — | no |
| Validation/QC — who reviews | CT staff; PE review own work; CT additional review | PO §2.3; review queue; entity review rows | VERIFIED / SERVICE | internal | yes | yes | no |
| Validation/QC — PE own review/QC | Yes | PO §2.3; entity review/QC rows | VERIFIED / SERVICE | entity (partial) | yes | yes | PE validation scope |
| Validation/QC — CT additional QC | Yes | PO §2.3; internal QC queue | VERIFIED / SERVICE | internal | yes | yes | no |
| Validation/QC — fail path | Routed back for correction | findings → rework; QC reject | VERIFIED / IMPLEMENTED | internal | yes | — | no |
| Approval — customer review | Part of workflow; UI being completed | PO §12; `customer-review` endpoint; NO UI (audit A-2) | C — BACKEND-ONLY | none | yes | — | approver role |
| Approval — what approval means | Confirms item final; recorded | `customer_review` stamps approved/rejected | VERIFIED (backend) | none | yes | — | no |
| Approval — what customer sees | Item, source, data, mapping, factor, calc, evidence | item workspace (signed) + evidence endpoints | VERIFIED (backend) | none | yes | — | no |
| Approval — reject | Requires reason; routes to mapping | `customer_review_item` (422 without reason; target mapping) | VERIFIED (backend) | none | yes | — | no |
| Approval — audit record | Approval recorded with evidence | customer_review stamps + audit | VERIFIED (backend) | none | yes | — | no |
| Approval — who can approve | Currently any org member via API; final rule PO decision | `require_org_member` on customer-review | VERIFIED (current) | none | yes | — | **approver role** |
| Evidence — trace to source | Result→…→source document | D33 evidence endpoint; reverse lookup | VERIFIED / IMPLEMENTED | evidence panel | yes | — | no |
| Evidence — what retained | source, extraction, mapping, factor, calc, validation/QC, approval | D33 evidence record fields | VERIFIED / IMPLEMENTED | panel | yes | — | no |
| Evidence — page/line | source_page where available | D33.1 source_page; line items | VERIFIED | partial | yes | — | no |
| Evidence — factor/calc/QC history | shown in record | evidence record + stamps | VERIFIED | panel | yes | — | no |
| Evidence — immutable | Finalized snapshots read-only | PO §7.3; snapshot design | VERIFIED | — | yes | — | no |
| Reports — types | Annual emissions report (structured 12-section) | `v3_reports.py SUPPORTED_REPORT_TYPES` ("annual") | VERIFIED / IMPLEMENTED | Reports page | yes | — | no |
| Reports — status | queued/generating/ready/failed | REPORT_STATUSES | VERIFIED / IMPLEMENTED | status badges | yes | — | no |
| Reports — export data | emissions + documents CSV/JSON | `v3_exports.py` (/emissions.csv, /emissions.json, /documents.csv) | VERIFIED / IMPLEMENTED | export buttons | yes | — | no |
| Reports — PDF | Backend endpoint exists; no portal button yet | `/api/v3/reports/{id}/pdf`; audit R-1 | C — BACKEND-ONLY | none | yes | — | no |
| Reports — Excel export | Not offered; CSV yes | exports surface (CSV/JSON only) | NOT ESTABLISHED (Excel export) | no | no | — | no |
| Reports — content | built from validated results | report generator | VERIFIED | — | yes | — | no |
| Reports — regenerate/versions | tracked versions | report versions | VERIFIED / IMPLEMENTED | versions | yes | — | no |
| Consultants — multi-org | Active grants per org | `consultant_auth.py` (D15/D19); `consultant_clients` active | VERIFIED / IMPLEMENTED | client switcher | yes | — | no |
| Consultants — switching | Active-client banner + switcher | ConsultantPage | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| Consultants — what they see | portfolio, processing status, reports, issues, messaging, branding | `v3_consultants.py`; ConsultantPage | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| Consultants — process data | Not currently; decision pending | no extraction workspace for consultants; blueprint C-1 | NOT ESTABLISHED (currently) | no | no | — | **consultant model** |
| Consultants — reports | Yes | client reports | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| Consultants — evidence | Via reports; deeper access pending | reports contain evidence; no direct evidence endpoint for consultants | PROPOSED | partial | partial | — | consultant model |
| Consultants — manage customer org | No | no such endpoints | VERIFIED | no | no | — | no |
| Consultants — separation | Active-client grant model; RLS is_org_consultant | consultant_auth + RLS | VERIFIED | yes | yes | — | no |
| PE — what it is | Approved external processing team | ADR/PO §3.1; `processing_entities` | VERIFIED | ops tab | yes | — | no |
| PE — work | extraction, mapping, validation, review, QC via portal | PO §2.3; entity workspace | VERIFIED / SERVICE | entity workspace | yes | yes | PE validation scope |
| PE — see documents | View assigned docs via portal | entity workspace (unsigned file refs); D32 portal-only intent | VERIFIED (intent) / BROKEN (viewer, audit E-1) | broken viewer | partial | — | no |
| PE — download documents | NO — enforced | storage RLS org-member-only; signed-url org-member gate; entity payloads unsigned (PE security audit; audit F) | VERIFIED — ENFORCED | n/a | n/a | — | no |
| PE — access control | assignment + role + entity scope | `require_entity_scope`, `_entity_workspace_guard`; entity RLS | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| PE — clarify | Request clarification; CT mediates | `entity_extraction_clarify`; issues storey | VERIFIED (backend) / C (no triage UI, audit I-1) | issue create | yes | — | no |
| PE — direct customer comms | No (messaging structurally denies PE) | `v3_messaging.py` (PE denied; RLS no entity storey) | VERIFIED | n/a | yes | — | no |
| Human-assisted — extraction service | Yes, via CT staff/PE | PO §2.3, §5.3; extraction audit (production path human-assisted) | VERIFIED / SERVICE | — | yes | yes | no |
| Human-assisted — data cleaning/mapping | Yes | PO §2.3 (mapping by PE/CT) | VERIFIED / SERVICE | — | yes | yes | no |
| Human-assisted — review/QC | Yes | PO §2.3 | VERIFIED / SERVICE | internal | yes | yes | no |
| Human-assisted — assisted/managed processing | Service model includes it | BillingPage (assisted/managed orders); D37 | VERIFIED (billing surface) | billing page | yes | terms | no |
| Human-assisted — automated vs human | Production workflow human-assisted; automation planned | extraction audit | VERIFIED | — | — | — | no |
| Security — who can access | members/CT staff/PE assigned/consultants active | auth model + RLS | VERIFIED | — | — | — | no |
| Security — documents private | private bucket + signed URLs | D32 migration; storage RLS | VERIFIED | — | — | — | no |
| Security — PE no download | enforced | see PE download row | VERIFIED | — | — | — | no |
| Security — access control | roles/scopes/assignment + RLS | RLS migrations; operations_auth | VERIFIED | — | — | — | no |
| Security — org separation | multi-tenant isolation | rc2 tenant policies; audits | VERIFIED | — | — | — | no |
| Security — audited | evidence access + processing actions recorded | audit trail; evidence.access audit | VERIFIED | — | — | — | no |
| Security — retention | being finalised | PO §8.1 (no retention architecture yet) | NOT ESTABLISHED | — | — | — | retention decision |
| Security — certifications (ISO/GDPR) | Not published | regulatory audit (no certification claims) | NOT ESTABLISHED | — | — | — | legal review |
| Security — data residency | UK-first, EU/EEA gradual; no verified guarantee | PO §1.1; regulatory audit (region not attested) | VERIFIED (launch intent) / NOT ESTABLISHED (guarantee) | — | — | — | residency decision |
| Security — compliance guarantee | None | no such claim | NOT ESTABLISHED | — | — | — | — |
| Org — multiple members | yes | org members model | VERIFIED / IMPLEMENTED | Members tab | yes | — | no |
| Org — roles | Owner/Admin/Member/Viewer | `organization_members.role` CHECK | VERIFIED | members tab | yes | — | **Viewer perms** |
| Org — consultant multi-org | yes | see consultant rows | VERIFIED | yes | yes | — | no |
| Org — PE access multiple customers | assigned work only | entity scope | VERIFIED | — | — | — | no |
| Billing — plan/credits | plan + credits model | `v3_billing.py`; BillingPage | VERIFIED / IMPLEMENTED | billing page | yes | — | no |
| Billing — credits | credit unit for processing | billing/credits endpoints | VERIFIED | yes | yes | — | no |
| Billing — assisted | estimate→approve→work | `createAssistedEstimate`, `approveBillingOrder` | VERIFIED / IMPLEMENTED | billing page | yes | — | no |
| Billing — managed | managed order request | `createManagedOrder` | VERIFIED / IMPLEMENTED | billing page | yes | — | no |
| Billing — usage/orders visibility | plan, credits, orders | BillingPage fields | VERIFIED / IMPLEMENTED | yes | yes | — | no |
| Billing — pricing | not published; confirm with CarbonTally | no price data in repo | NOT ESTABLISHED | — | — | — | pricing decision |
| Does not do — auditor/verifier/certifier | Not offered | product scope; PO §10.4 positioning | VERIFIED (scope) | — | — | — | no |
| Does not do — compliance guarantee | Not offered | no such claim anywhere | NOT ESTABLISHED | — | — | — | no |
| Does not do — legal advice | Not offered | scope | VERIFIED | — | — | — | no |
| Does not do — emission reduction guarantee | Not offered | scope | VERIFIED | — | — | — | no |
| Does not do — automated OCR | Not in customer workflow | extraction audit | VERIFIED | — | — | — | no |
| Does not do — every country factors | Only DEFRA/SEAI/custom | PO §6.1 | VERIFIED | — | — | — | no |
| Does not do — public integrations | None established | no integration code | NOT ESTABLISHED | — | — | — | no |
| Does not do — accounting/ERP | Not a general system | scope | VERIFIED | — | — | — | no |
| Getting started — 8 steps | journey mapping | workflow model + onboarding | VERIFIED (model) | partial | yes | yes | no |
| Troubleshooting answers | reflect actual behavior | see individual rows above | VERIFIED | — | — | — | — |

---

## 4. Capability vs Service vs Future

### 4.1 Available now (customer-facing)

- Upload PDF, image (JPG/PNG/GIF/WebP), CSV, Excel (XLS/XLSX).
- View documents and their linked emissions; reverse evidence lookup.
- View processing batches and items (status).
- Manual single-row emissions calculation with factor matching and result.
- Evidence record panel per result (source/extraction/mapping/factor/
  calculation/result).
- Annual emissions report generation (queued/generating/ready/failed),
  versions tracked, JSON download.
- Export emissions and documents as CSV/JSON.
- Create and view customer issues.
- Customer↔consultant messaging.
- Organisation workspace: profile, members, facilities, suppliers, security.
- Billing: plan, credits, orders (assisted estimate + managed), order
  approval.
- Notifications centre.
- Consultant portfolio + active-client workspace (status, reports, issues,
  messages, branding).

### 4.2 Available through CarbonTally-assisted processing (human-assisted service)

- Extraction of data from documents (PDF, scans, images, spreadsheets).
- Data cleaning and mapping to activities, units, facilities.
- Validation, review and QC (by processing partner then CarbonTally).
- Mediated clarification (entity → CarbonTally → customer).
- Assisted and managed processing arrangements (via billing orders).

### 4.3 Backend capability / UI pending

- Customer final approval / rejection of processed items
  (`customer-review` endpoint; no UI).
- Customer custom emission factor management (full API; no UI).
- Customer item-level processing + evidence detail (item workspace API; no
  customer UI).
- Factor catalogue / provenance browsing (data exists; no UI).
- Report PDF download (endpoint exists; no button).
- Entity clarification triage for CarbonTally staff (API partial; no ops
  triage UI).
- CSV/Excel self-service mapping (capability; legacy UI dead, V3 UI absent).

### 4.4 Planned / future

- Automated OCR and image extraction in the customer workflow (PO §5.2
  direction to recover/verify historical extraction).
- Report PDF download button in portal.
- Issue conversations (customer↔CarbonTally).
- Admin/control-plane sections (AI providers, retention, factor governance).
- Excel export.
- Viewer-role final rules and role-gated navigation (pending decisions).

### 4.5 Not offered / not established

- Independent emissions assurance / third-party audit / regulatory
  certification.
- Guaranteed compliance or legal/regulatory outcomes.
- Legal advice.
- Guaranteed emission reductions.
- Automated OCR in the customer workflow today.
- All countries' emission factors (only DEFRA, SEAI, custom).
- Public integrations (accounting/ERP/etc.).
- Security certifications (ISO 27001, GDPR certification).
- Verified data-residency guarantee.
- Bulk historical data import from other systems.
- Excel export of results.

---

## 5. Claim audit notes (FAQ quality control)

1. Every FAQ answer maps to at least one matrix row. Answers without a row
   (plain-language definitions) are flagged `n/a` and make no product claim.
2. No claim of automated OCR in the customer workflow: the extraction audit
   confirms OCR is legacy and not production-wired (PO §5.4).
3. No claim of a specific residency guarantee: the regulatory audit confirms
   region is not attested; FAQ says "confirm with CarbonTally".
4. No certification claims: FAQ explicitly says certifications are not
   published and flags legal review.
5. Pricing: no prices invented; FAQ uses "confirm with CarbonTally".
6. Processing Entity no-download is stated as enforced (verified at storage
   RLS, signed-URL gate and unsigned entity payloads).
7. "Who can approve" and "Viewer permissions" are marked as decisions pending
   (PO DECISION REQUIRED), not asserted.
8. Consultant processing and evidence access marked as decision pending.
9. Anything marked NOT ESTABLISHED is either excluded from the FAQ or
   explicitly disclaimed there.

---

## 6. PO decisions surfaced by this matrix

1. Exact Viewer permissions (matrix: Org — roles).
2. Customer processing participation / self-service mapping (Documents,
   Mapping, Processing rows).
3. Consultant operating model (consultant rows).
4. Customer approval role(s) (Approval — who can approve).
5. PE validation/review/QC action set (Validation/QC — PE rows).
6. Custom factor editors (Factors — custom).
7. Retention periods (Security — retention).
8. Data residency commitment (Security — residency).
9. Pricing / commercial terms (Billing — pricing).
10. Assisted/managed processing service terms (Human-assisted — terms).
