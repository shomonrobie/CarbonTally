# CarbonTally V3 — Product Owner Decision Register
## Version 1 — 26 August 2026

This document is the current Product Owner baseline for CarbonTally V3.
It consolidates decisions made across the CarbonTally V3 conversations and
the completed Cline / OpenHands audit findings available at the time of
creation.

**Authority:** Product Owner decisions made in the CarbonTally V3 project
conversation.

---

# 1. Product and launch decisions

## 1.1 Initial market — LOCKED

CarbonTally will target:

- UK
- Ireland
- EU/EEA

Launch will be gradual rather than an unrestricted global launch.

## 1.2 Public production signup — LOCKED

Public production signup is initially closed.

Prospective customers may apply/request access or beta access.

Production onboarding remains controlled by CarbonTally.

## 1.3 Beta — LOCKED

Obsolete beta entry points and beta infrastructure/tables should be removed
if they are not required by the current V3 architecture.

A beta application/request mechanism may remain where intentionally required.

---

# 2. Identity and access

## 2.1 One account, one role — LOCKED

One person has one CarbonTally account and one role.

A single account must NOT simultaneously operate as:

- Processing Entity Staff
- Customer Organisation member
- Consultant
- another conflicting role

Do not implement dual-scope identity.

## 2.2 Processing Entity assignment — LOCKED

CarbonTally controls Processing Work assignment.

Assignment may be performed by:

- authorized CarbonTally Staff
- authorized automated/system controls

A Processing Entity cannot freely discover or claim Customer Organisation
work.

## 2.3 Processing Entity responsibilities — LOCKED

Processing Entities may perform:

1. Human Extraction
2. Mapping
3. Validation
4. Review
5. QC

After Processing Entity review/QC, CarbonTally performs its own secondary
Validation/Review/QC before submission to the Customer Organisation.

The Customer Organisation has final approval authority.

Preferred terminology for the quality chain:

Processing Entity QC
→ CarbonTally QC
→ Customer Final Approval

---

# 3. Processing Entity and international processing

## 3.1 Processing Entity legal model — LOCKED PRODUCT MODEL

The intended commercial/legal operating model is:

Customer Organisation
→ CarbonTally
→ Processing Entity
→ Processing Entity Staff

Processing Entities are intended to operate as CarbonTally subprocessors,
subject to legal counsel confirmation and the appropriate contractual and
international-transfer framework.

## 3.2 Processing location — LOCKED PRODUCT POLICY

CarbonTally controls the processing architecture.

Customers do not normally choose individual Processing Entities or
processing countries as ordinary product settings.

However, CarbonTally must still honour applicable contractual, legal and
customer-specific restrictions.

## 3.3 No document downloads — LOCKED

Processing Entity Staff must NOT download Customer Organisation source
documents.

They may access assigned Processing Work through the CarbonTally portal
and perform authorized:

- extraction
- mapping
- validation
- review
- QC

They must not:

- download source documents
- store customer documents locally
- receive raw storage credentials
- access arbitrary customer storage objects

This is a product/security policy and does not by itself eliminate
international-transfer obligations.

## 3.4 Bangladesh Human Processing — POLICY GATED

Bangladesh-based Processing Entities may eventually be used for Human
Processing if the required legal, contractual, transfer, security and
operational controls are established.

Bangladesh processing is NOT automatically prohibited.

Remote access by Bangladesh Processing Entity Staff may still constitute an
international transfer/access under applicable data-protection law even when
documents remain on CarbonTally-controlled UK/EU infrastructure.

Required before real Bangladesh Processing Work:

- Processing Entity due diligence
- Processing Entity agreement
- appropriate DPA/subprocessor terms
- UK transfer mechanism where applicable
- EU SCC mechanism where applicable
- UK/EU transfer assessment
- Bangladesh legal review
- supplementary security measures
- staff confidentiality/training
- access controls
- incident controls
- deletion/return controls
- audit evidence
- customer contractual/authorization requirements where applicable

## 3.5 Special/high-risk data — PROVISIONAL POLICY

Default position: do not send special-category/high-risk personal data to
Bangladesh Processing Entities until enhanced legal and operational controls
have been established and approved.

This requires counsel confirmation before becoming a final legal policy.

---

# 4. AI processing

## 4.1 Internal/local AI first — LOCKED PRODUCT PRINCIPLE

CarbonTally should prefer:

- deterministic Python processing
- internal/local AI
- controlled internal extraction tools

before using external AI providers for customer-data extraction.

External AI is not the default.

## 4.2 External AI providers — CONTROLLED

External AI providers may be used only through an approved/configurable
provider architecture.

The eventual Admin Dashboard should be able to configure approved AI
providers and their applicable controls.

AI provider processing must be governed separately from Bangladesh Human
Processing.

Do not combine the two supplier/transfer models.

---

# 5. Extraction and ingestion

## 5.1 Existing structured-data capabilities — LOCKED

CarbonTally already has core support for:

- CSV mapping
- Excel/XLS/XLSX mapping
- Customer Custom Emission Factors

These are existing product capabilities and must be preserved.

## 5.2 Historical document extraction — LOCKED ENGINEERING DIRECTION

CarbonTally had PDF/image extraction functionality early in development.

Do NOT assume that current V3 route gaps mean the historical functionality
never worked.

First:

1. locate historical extraction implementation;
2. locate historical tests;
3. locate sample inputs/expected outputs;
4. determine what still works;
5. identify what was lost or disconnected during V3 migration;
6. reuse/fix sound historical implementation.

Only rebuild functionality where the historical implementation is unsuitable.

## 5.3 Target extraction workflow — LOCKED

The intended product workflow is:

Upload
→ File Classification
→ PDF/Image Processing
→ OCR when required
→ Internal/Local AI-assisted extraction where appropriate
→ Human correction
→ Mapping
→ Processing Entity Validation/Review/QC
→ CarbonTally Validation/Review/QC
→ Calculation
→ Evidence
→ Customer Final Approval

## 5.4 Production capability language — LOCKED

Do not publicly claim automated PDF/image/OCR/AI capabilities beyond what is
actually production-wired and verified.

Do not confuse:

- engine exists
- route exists
- route is wired
- end-to-end tested
- production verified

---

# 6. Emission-factor architecture

## 6.1 Factor sources — LOCKED

CarbonTally supports/targets a unified factor architecture containing:

- DEFRA factors
- Irish/SEAI factors
- Customer Custom Emission Factors

These are not separate product architectures.

## 6.2 Custom factors — LOCKED

Customers can create their own emission factors.

This is already implemented and must be preserved.

## 6.3 Factor resolution — LOCKED PRODUCT DIRECTION

CarbonTally should resolve the appropriate factor using relevant context
such as:

- Customer Organisation
- factor configuration
- country
- reporting year
- activity
- factor source/set

Customer-specific/custom factor configuration must not be accidentally
overridden by an automatic DEFRA/SEAI selection.

## 6.4 Factor provenance — LOCKED

The selected factor, source/set, reporting year/version where available,
and relevant mapping/calculation provenance must remain traceable.

---

# 7. Traceability and evidence

## 7.1 Row-level traceability — LOCKED

CarbonTally already has row-level traceability.

Do not replace it with a new parallel evidence system without a demonstrated
need.

The intended chain is:

Source Document
→ Source Row/Evidence
→ Extracted Activity
→ Mapping
→ Selected Emission Factor
→ Calculation
→ Result

## 7.2 Human corrections — LOCKED

When a human changes extracted/mapped information, CarbonTally should retain
the original value and the corrected value with reviewer/time/reason
information where supported by the existing audit model.

## 7.3 Final evidence — LOCKED

Finalized calculation evidence should be immutable.

---

# 8. Retention

## 8.1 Retention model — LOCKED PRODUCT DIRECTION

Retention should eventually support customer-specific policies.

Do not implement a new retention architecture until legal/contractual
minimums, evidence requirements, and backup implications are established.

---

# 9. Legacy application and routes

## 9.1 Legacy routes — LOCKED

Remove all obsolete legacy application/document routes.

Do not merely hide unsafe legacy routes in the UI.

Before removal, verify whether any current V3 feature depends on them.

Legacy public/unauthenticated document/upload surfaces must not remain
available to real customer personal data.

## 9.2 Beta infrastructure — LOCKED

Remove obsolete beta entry points/tables if they are not required by the
current V3 architecture.

---

# 10. Public website

## 10.1 New OpenHands website — DECIDED

The newly created OpenHands public-facing website is intended to replace
the current public-facing CarbonTally website after independent review and
approval.

Do not replace the current production website before review.

## 10.2 Temporary isolation — DECIDED

The new website may remain in an isolated OpenHands project/repository while
being reviewed.

Once approved, it should be integrated into the canonical CarbonTally
deployment structure rather than creating a permanently duplicated public
codebase unless a later architecture decision says otherwise.

## 10.3 Website messaging — LOCKED

The public website should communicate:

- what CarbonTally does
- services offered
- target users/customers
- processing model
- relevant trust/security information
- pricing where approved
- contact/access/beta mechanism

It should NOT expose CarbonTally's internal development progress as a
development status dashboard.

Do not tell visitors things such as:

- "backend 80% complete"
- "OCR still being built"
- "Phase X complete"
- internal engineering roadmap

However, public capability claims must remain truthful and must not claim
unverified automated functionality.

## 10.4 Positioning — EVOLVING

CarbonTally's market positioning remains intentionally evolving.

Do not prematurely freeze the company into a narrow "carbon accounting
software" description.

Current conceptual direction:

emissions data processing / emissions data processing middleware, producing
traceable validated emissions results.

---

# 11. Admin Dashboard

## 11.1 Admin configuration — LOCKED PRODUCT DIRECTION

The Admin Dashboard should eventually be the central control plane for
configurable operational policy, including as appropriate:

- Processing Entities
- Processing Entity approval/status
- processing policies
- AI providers
- factor sets
- customer-specific retention
- subscriptions/billing
- feature controls
- operational policies

Do not hard-code configurable business policy where a controlled Admin
configuration is the intended product model.

---

# 12. Customer final approval

Customer approval remains the final customer-facing approval step.

The intended quality chain is:

Processing Entity
→ CarbonTally
→ Customer

Specifically:

Processing Entity Extraction/Mapping/Validation/Review/QC
→ CarbonTally Validation/Review/QC
→ Customer Final Approval

---

# 13. Current engineering priorities

The following should be treated as the next engineering priorities, in
rough order:

1. Verify and remove all legacy application/document routes.
2. Verify current onboarding/demo authentication and post-login routing.
3. Recover/audit historical PDF/image extraction before rebuilding.
4. Verify production CSV/Excel mapping remains intact.
5. Verify Customer Custom Emission Factors remain intact.
6. Verify production DEFRA factor data.
7. Verify production Irish/SEAI factor data.
8. Verify factor resolution across DEFRA/SEAI/custom factors.
9. Improve/verify unit normalization.
10. Verify the real document → extraction → mapping → calculation →
    persistence path.
11. Preserve and verify row-level traceability.
12. Implement retention controls after policy/legal requirements are fixed.
13. Implement Processing Entity no-download portal controls and enforcement
    where not already complete.
14. Build the approved Processing Entity legal/operational gate.
15. Build controlled AI-provider architecture only after internal extraction
    capability has been recovered/verified.

---

# 14. Demo, blog and public-content integration

## Demo data

Existing demo data must remain intact unless a deliberate migration is
approved.

The known demo result:

10,732.4 kg CO2e

must not be treated as proof of a production end-to-end document pipeline
unless it is independently reproduced through the current production path.

The next meaningful demo milestone is a real V3 processing demonstration
that exercises:

CSV/Excel and/or real document input
→ extraction
→ mapping
→ factor selection
→ calculation
→ persistence
→ evidence
→ review

## Blog

The CarbonTally blog should be integrated as a public content layer after
the public website is approved.

Blog integration should not block the core security/product readiness work.

The blog should use customer-facing educational content and should not expose
internal development progress or unverified product capabilities.

---

# 15. Onboarding status

Cline's latest completion report indicates that:

- reproducible demo/test identities were added;
- invitation acceptance was implemented and tested;
- authoritative post-login routing was implemented;
- legacy `/dashboard/*` is no longer the primary V3 route;
- onboarding/invitation/context tests passed.

However, a real browser acceptance test using the actual demo credential
still needs to be performed from the user-facing login page.

Therefore:

**Onboarding is engineering-fixed according to the Cline report, but
user-facing demo-login acceptance is NOT yet considered finally signed off
until we manually verify it.**

If the supplied demo credential still fails, do not redesign onboarding
immediately. Capture:

- login request/response
- auth state
- redirect
- destination route
- organization/context
- browser console/network errors

and then fix the actual remaining defect.

---

# 16. Evidence sharing between OpenHands and Cline

OpenHands runs in isolated projects. Therefore reports created there are not
automatically visible to Cline.

Operational rule:

OpenHands audit
→ report
→ `docs/audit/openhands/`
→ controlled Git commit/push
→ Cline reads report
→ implementation

Audit agents should push only their intended audit/report artifacts when
explicitly instructed.

Do not allow an audit report push to silently include unrelated application
changes.

---

# 17. Open decisions requiring future confirmation

The following are not yet final legal advice and require appropriate counsel
or evidence:

- exact UK controller/processor/subprocessor structure for each customer
scenario;
- exact UK IDTA/Addendum requirements;
- exact EU SCC module and transfer mechanism;
- UK/EU transfer assessment;
- Bangladesh legal position;
- special-category/high-risk data policy;
- customer DPA wording;
- Processing Entity agreement;
- retention periods;
- sector-specific NHS/HSE/financial-services requirements;
- external AI provider terms and geographic processing;
- final public privacy/security claims.

---

# 18. Product Owner principle

CarbonTally should not solve legal uncertainty by inventing technical
features.

First determine:

LEGAL REQUIREMENT
→ CONTRACTUAL REQUIREMENT
→ CUSTOMER/PROCUREMENT REQUIREMENT
→ OPERATIONAL CONTROL
→ SECURITY CONTROL
→ PRODUCT POLICY
→ ENGINEERING IMPLEMENTATION

Only then implement the necessary engineering controls.

---

# 19. Canonical terminology

Use CarbonTally's established terms:

- Customer Organisation
- Processing Entity
- Processing Entity Staff
- Processing Work
- Human Processing
- Human Review
- Validation
- QC
- Evidence
- Emission Factor
- Custom Emission Factor
- Factor Matching
- Calculation
- CarbonTally Staff

Do not casually replace these with generic terms such as "client", "worker",
"outsourcing company", or "BPO worker" when discussing the CarbonTally
architecture.

---

# 20. Immediate next milestone

Before another large engineering phase:

1. Push the completed OhD extraction audit into
   `docs/audit/openhands/`.
2. Push the completed OhOr regulatory/Processing Entity reports into
   `docs/audit/openhands/`.
3. Preserve this Product Owner Decision Register as the current decision
   baseline.
4. Verify the actual demo login manually.
5. Perform the historical extraction recovery audit.
6. Review the new OpenHands website independently.
7. Then issue a new Cline engineering prompt based on the consolidated
   evidence.

---

## END OF PRODUCT OWNER DECISION REGISTER
