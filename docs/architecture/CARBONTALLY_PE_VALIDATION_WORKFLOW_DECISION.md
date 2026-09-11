# PE Validation Workflow Decision — Design/Decision Record

Status: DESIGN ONLY — no implementation. WS4 remains open pending PO approval.

## 1. Current state

CURRENT FACT — PE-origin work cannot legally reach calculation through the real
PE UI: the frozen state machine requires `mapped → validated → calculating →
calculated`, but `backend/api/v3_pe.py` exposes start/extract/map/calculate,
PE Review and PE QC — no validate action. Browser E2E confirmed the internal
path (`pending → … → validated → calculated`) works; the PE path is blocked at
`mapped`.

## 2. Current validation contract

CURRENT FACT — `POST /api/v3/ops/items/{id}/validate` runs
`validate_processing_item`; clean items transition `mapped → validated`,
blocking findings route to `mapping` and open `issues`. Authorization:
internal staff `can_review` (reviewer). The reviewer-gated human validate is
the only existing resolution path from `mapped`.

## 3. Existing internal workflow

CURRENT FACT — Internal (browser-verified in WS4 remediation): Data-entry
operator (`can_process`) extracts and maps → Internal Reviewer (`can_review`)
validates → operator calculates → reviewer later submits for CarbonTally QC
(`can_qc`, separate role) → customer review/approval. Internal precedent:
reviewer both validates (pre-calculation) and submits the review
(post-calculation); the independent control gates are CarbonTally QC and
customer approval.

## 4. Existing PE workflow

CURRENT FACT — PE roles (PE-ROLE-001, frozen): Data Entry Operator (`process`),
Reviewer (`review`), QC Specialist (`qc`), Admin (full PE set). PE Review is
reviewer-gated; PE QC is qc-gated; both were browser-verified on items already
at `calculated`. PE-origin processing happens inside the entity trust domain;
CarbonTally control is applied at CT QC and customer approval.

## 5–7. Options

PROPOSED OPTION A — PE Reviewer performs validation.
Operator extracts/maps → PE Reviewer validates (`mapped → validated`) →
operator (or admin) calculates → PE Reviewer performs PE Review → PE QC
Specialist performs PE QC → internal CT QC → customer review/approval.
- Roles/capabilities: sufficient today (reviewer has `review`; no new role).
- API/UI: add PE validate endpoint (mirror of ops validate, gated by PE
  `review` capability) + PE workbench Validate control at `mapped`. State
  machine, RLS, schema, D38/D39/D40 unchanged.
- Security/SoD: validation is a data-completeness gate; PE Review is the
  entity's approval gate; PE QC is a different role; CT QC and customer
  approval are outside the entity. Same-role validate+PE Review mirrors the
  accepted internal precedent and does not grant QC/CT QC/customer authority.
- Audit: validate/calculate/review/qc each already write provenance columns
  and/or audit rows with actor + entity + origin + timestamps.
- Operational: keeps processing inside the PE trust domain; no handoff churn.

PROPOSED OPTION B — CarbonTally internal staff validates PE-origin items.
Internal reviewer (can_review) validates after PE mapping.
- Consistent with today's endpoint (zero backend work for the gate itself) but
  breaks the PE trust-domain operating model, adds inter-party handoff and
  CarbonTally workload at every PE item, and blurs audit attribution between
  the PE's own QC chain and CarbonTally's independent CT QC. Not recommended.

PROPOSED OPTION C — Automated validation.
- The validation engine exists (`validate_processing_item`) but there is no
  durable worker that performs `mapped → validated`; calculation remains a
  human-triggered stage. Introducing automation implies job/worker
  architecture and changes to the approved human-gated pipeline. Larger
  change; can be revisited independently of WS4.

## 8–11. Analyses (summary)

- Separation of duties: Option A keeps data entry (operator) separate from
  validation/review (reviewer) and from QC (qc_specialist) and from
  CarbonTally control (internal CT QC / customer). Same-role validate + PE
  Review duplicates the internal pattern; the real control separation is
  operator→reviewer→qc→CT QC→customer.
- Security: Option A cannot bypass CT QC or customer approval; PE roles never
  gain CarbonTally authority (pe_auth trust-domain checks).
- Auditability: provenance columns + audit events identify validator,
  calculator, PE reviewer, PE QC, CT QC actor, entity, origin, timestamps.
- API/UI/DB impact: Option A = one PE endpoint + one workbench control;
  no schema/RLS/state-machine/role change.
- Prior decisions: PE-ROLE-001 defines the frozen PE role set; no authoritative
  prior decision resolves who owns validation for PE-origin work.

## 12–20. Recommendation and impact

RECOMMENDATION — **Option A: PE Reviewer performs validation** (with Admin
retaining the full PE-domain capability, as today). Rationale: mirrors the
accepted internal workflow, uses only frozen roles/capabilities, preserves the
PE trust-domain operating model and CarbonTally's independent CT QC/customer
control, and is the minimum change (one endpoint + one control, no migration).

PO DECISION REQUIRED — 1) Adopt Option A/B/C (or defer PE full E2E).
2) If A: authorize adding the PE validate endpoint (PE `review` capability
mirroring ops `can_review`) and the PE workbench Validate control.

WS4 impact — WS4 final PE E2E cannot pass until a PE validate path exists
(decision above). WS5 impact — none unless the option changes roles.

No data/schema/factor/role/user changes made. Baselines verified: factors
7,049; migrations 45.

---

# IMPLEMENTATION RESULT (Option A — approved & implemented)

## Files changed

- backend/api/v3_pe.py — added POST /api/v3/pe/items/{id}/validate (PE
  Reviewer, CAP_REVIEW; mapped→validated | mapped→mapping on blocking findings;
  canonical validate engine reused; immutable audit event pe_validate:*).
- frontend/src/v3/api.js — entityValidateItem client.
- frontend/src/v3/ops/PEEntityItemPage.jsx — Validate (PE Review) control shown
  only at status mapped for members whose frozen PE role grants review; result
  notice/blocking alert; workbench refresh after saves.
- frontend/src/v3/ops/ExtractionPanel.jsx — entity-mode Calculate gated to
  legal states (validated/calculating/calculated); no mapped→calculate.

No migration, schema, RLS, role, capability, state-machine, D38/D39/D40 or
CT QC change.

## Browser E2E (disposable PE fixture, from pending, real UI)

PASS PV1 operator cannot see Validate (no review cap); PV2 PE operator reached
mapped via UI; PV3 stale banner cleared after mapping refresh; PV4 Calculate
unavailable at mapped; PV5 Reviewer sees Validate at mapped; PV6 validate
request HTTP 200; PV7/8 Validated notice + status validated; PV10 Calculate
enabled at validated; PV11 calculate HTTP 200 result persisted; PV12 status
calculated.

## Authorization negatives (live API)

403 PE operator validate; 403 beta-PE (cross-entity) validate; 403 internal
staff via PE contract; 403 customer via PE contract; 409 validate on item
beyond mapped (calculated).

## Integrity

e2e auth users 0 · organizations 975 · items 260 · batches 56 · assignments 0
· conversations 34 · messages 52 · participants 62 · notifications 0 ·
emission_factors 7049 · migrations 45. Frontend production build passes.
