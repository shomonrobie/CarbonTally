# CARBONTALLY V3 — BANGLADESH PROCESSING ENTITY LEGAL, POLICY & OPERATIONAL RESEARCH

**Status:** Independent read-only policy / legal / operational research
**Date:** 26 August 2026
**Baseline:** `d4dcca1eb11f86bcae497815c8592d688a7e305f` (`origin/main`); isolated clone at `/tmp/carbontally-independent-audit`; active developer workspace untouched
**Profile used:** OpenRouter
**Mode:** NOT legal advice. NOT implementation. Repository unchanged.
**Source note:** Where authoritative primary sources were unreachable (some Bangladesh official portals, some UK/EU page variants, some sector sources), the gap is stated explicitly rather than filled with inference. Bangladesh statutory position is uncertain from the sources available to this research as of this date.

> **Credential discovered — value not reproduced.**

---

## 1. Executive Summary

CarbonTally's ratified architecture (ADR-V3-001 Option B, D22) treats Bangladesh-based Babui Limited as a first-class **Processing Entity** / **Human Data Processing Entity**, not as a synthetic internal unit, and permits one Customer Organisation to have work assigned to CarbonTally internal staff and/or to external Processing Entities simultaneously, with assignment controlled by CarbonTally staff.

The core legal question — whether a UK or EU customer's document can lawfully be made accessible to a Bangladesh Processing Entity for Human Processing — is **not automatically prohibited** by UK or EU GDPR alone, but it is **conditionally permitted only with a valid transfer mechanism, a documented assessment, and appropriate contractual and operational safeguards**.

Classifying every conclusion (LAW / REGULATORY GUIDANCE / CONTRACT / PROCUREMENT / BEST PRACTICE / PRODUCT POLICY):

- **UK:** A Customer Organisation → CarbonTally → Bangladesh Processing Entity flow involving customer personal data is ordinarily a **restricted international transfer** under UK GDPR (not an automatic exemption). The data exporter is normally CarbonTally when processing on the customer's instructions. Mechanisms: **UK IDTA / UK Addendum** (UK GDPR appropriate safeguards; ICO guidance verified live). UK **transfer risk assessment / data protection test** is required when not covered by an adequacy decision. **Bangladesh is not confirmed as adequate** in the verified ICO adequacy page content.
- **EU/EEA:** Same functional analysis; **EU Standard Contractual Clauses** (verified EC page); EU **Transfer Impact Assessment (TIA)** required per EDPB Recommendations 01/2020 (PDF verified live, 200, application/pdf, 1.34 MB). No blanket EU-localisation mandate exists.
- **Ireland:** No additional statutory data-residency rule found beyond EU GDPR + Irish Data Protection Act; HSE-specific requirements must be read from the applicable tender or contract, not invented from public pages.
- **Bangladesh:** **No authoritative text of a current Bangladesh Personal Data Protection Ordinance 2025 or Cyber Security Act 2025 was verified from the official portals (`bdlaws.minlaw.gov.bd`, `ictd.gov.bd`, `dpp.gov.bd`, `cabinet.gov.bd`) or the Government Gazette in this research.** The `bdlaws` index page loaded but keyword searches returned no hits; some portals block or return encoded content; some official sites use self-signed certificates or are unreachable. CarbonTally must not assume either "no law applies" or "law prohibits processing". Confirmation by Bangladeshi counsel is required.
- **Operating model:** **Model A (Processing Entity as CarbonTally's subprocessor)** is the most practical; **Model B (customer-approved named subprocessor)** adds customer-contract friction but strengthens transparency; **Model C (customer contracts directly with the Processing Entity)** is not recommended due to contractual fragmentation, liability ambiguity, and operational complexity.
- **Public claims:** CarbonTally's `DataSecurity.jsx`, pricing and architecture documents describe Babui Limited in Bangladesh, a "formal business and data-processing arrangement", ISO 27001 for Babui's operations, controlled workspace, mediated clarification (entity → CarbonTally, never direct customer ↔ entity), least-privilege processing, and that international-transfer requirements apply when data is made accessible outside the UK. These claims must be supported by contracts, assessments, and live controls — not by architecture intent alone.

**Critical distinction preserved:** CarbonTally's architectural term **Processing Entity** (ADR-V3-001, V3M-1, `processing_entities`) is not automatically one fixed legal classification. Depending on instructions, contract, and decision-making authority, a Bangladesh Processing Entity could be:

- a **subprocessor** (most common for Human Processing assigned by CarbonTally);
- another **processor** (if CarbonTally is itself a processor for the customer and delegates processing); or
- in exceptional cases, a **separate service provider / independent controller** for its own operational purposes — but not for the customer's document processing if CarbonTally controls assignment, requirements, and evidence.

The legal classification must follow actual processing activity, instructions, contract, and decision authority — not the CarbonTally label.

---

## 2. CarbonTally Operating Model (from repository evidence)

### 2.1 Customer Organisation

- Represented by `organizations` (tenant root), `organization_members` (roles: `owner`, `admin`, `member`, `viewer` per schema CHECK), `organization_metadata`, facilities, assets, suppliers.
- Customer does **not** receive an `organization_members` row for the Processing Entity (actor model §6, Glossary §9, Access Model §6.1, §17).
- Multi-tenancy: a single auth user can hold multiple org memberships, but V3 resolves one active org via `resolveV3Organization`.
- Processing Work originates from customer uploads (`organization_files` / `manual_extraction_items` / `customer_documents`) tied to an `organization_id`.

### 2.2 Processing Entity

- `processing_entities` table (`id`, `name`, `status`: `active | remediation | suspended | terminated`, `metadata JSONB`); `status='active'` required for access (`is_entity_member`).
- No company name hard-coded; Babui is a data row (Master v1 §65, §304, ADR-V3-001, Glossary §9).
- First-class domain per ADR-V3-001 Option B (dedicated table; not parent org + child; not synthetic).
- Lifecycle: active → remediation/suspended → terminated; never hard-deleted while referenced (FK `ON DELETE RESTRICT`); historical work / attribution retained (D22; Actor Model §16; Access Model §23).
- Contract metadata deferred (Q1); current `metadata JSONB` carries flexible contract / commercial details.

### 2.3 Processing Entity Staff

- `staff_profiles.entity_id IS NULL` = CarbonTally internal staff; populated = Processing Entity staff (positive NULL convention, ADR-V3-001 Q5).
- Staff roles from `staff_roles` (`operator`, `reviewer`, `qc_specialist`, `admin`) with `permissions` jsonb; not merged with org roles or consultant roles.
- Entity staff have **entity-scoped SELECT only** (`is_entity_member`) on `processing_entities`, `staff_profiles`, `manual_review_queue`, `upload_batches`, `issues`; write paths for claim / completion remain service-role / application in V3M-6.
- Entity staff must **never** receive broad customer-org access (D20; Access Model §38.7).

### 2.4 CarbonTally Staff

- `entity_id IS NULL`; may administer assignment, validation, QC, reviews, audits.
- Assignment is controlled by `require_internal_staff` + `can_manage_staff` + `can_process`; `assign_batch` accepts exactly one of `assigned_to` (internal operator) or `entity_id` (Processing Entity), with audit before → after (D22; `v3_operations.py`).
- Internal staff may review entity-produced output (`allow_entity_gate`) but entity staff do **not** run validation, review, or QC gates.

### 2.5 Processing Work

- Work order: `manual_extraction_batches` (batch-level, `entity_id` nullable FK → `processing_entities`; `organization_id` = customer; status `open` / `in_progress` / `qc_in_progress` / `qc_passed` / `completed` / `cancelled` / `failed`; `assigned_to` = internal operator or cleared for entity; `assigned_by`; assignment audit).
- Work item: `manual_extraction_items` (document within batch; `status` vocabulary `pending` / `extracting` / `extracted` / `mapping` / `mapped` / `validating` / `validated` / `calculating` / `calculated` / `customer_review` / `approved` / `rejected` / `qc_approved` / `qc_rejected` / `failed`; `extracted_data` / `mapped_data`; `calculated_emissions_kg_co2e`; `qc_by` / `qc_at` / `quality_score`; `customer_reviewed_by` / `customer_reviewed_at` / `customer_approved`; source linkage via `file_id` D33).
- Entity workspace: `/api/v3/ops/entities/{entity_id}/extraction/*` with `_entity_workspace_guard` + `_entity_checked_item`; only assigned batches / items visible; validation, review, QC blocked at API; clarification only through mediated `entity_extraction_clarify` (creates `issues` with `entity_id` and `manual_extraction_batch_id`, never customer-facing).
- Multiple entities per org: ratified (§6.1); a batch has exactly one active party (`entity_id` XOR `assigned_to` at assignment time); simultaneous internal + Entity A + Entity B is possible via separate batches.

### 2.6 Human Processing

- Public language (DataSecurity.jsx; Pricing; LandingPage): "Human processing when automation isn't enough"; "Controlled document viewer"; "Assigned Processing Job"; "Human extraction → Mapping → Validation → Calculation → Evidence".
- Actual model: Human Processing = Processing Entity staff performing extraction / mapping on assigned work items; validation, review, QC = CarbonTally internal staff; evidence = `calculation_snapshots` + `emissions_logs` + audit / domain events + source-file links (D33).
- **No direct customer ↔ entity communication** (Access Model §35, §38.8; glossary; architecture). Mediation: entity raises clarification → CarbonTally staff triage → customer-facing issue surface → outcome read back by entity through entity-scoped issue list.
- **Bangladesh specifically named** (DataSecurity.jsx §292–316): Babui Limited in Bangladesh, under formal business / data-processing arrangement; ISO 27001 certified for relevant operations; remote work permitted subject to contractual / confidentiality / security / access-control requirements; international-transfer requirements apply when data is made accessible outside the UK.

### 2.7 AI-assisted extraction

- Separate from Human Processing; `LLMClient` sends document text to a configured endpoint; production composition / policy not found; requires separate transfer / subprocessor / retention / training controls (not part of this research focus, but must not be conflated with Bangladesh Human Processing).

---

## 3. Required Decision Matrix

| Question | UK | Ireland | EU/EEA | Bangladesh Processing Entity | Classification | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| Is UK → Bangladesh a restricted transfer? | Yes (per ICO transfer rules) | n/a | n/a | Yes — exporter CarbonTally, importer Babui; mechanism + assessment required | Legal obligation (UK GDPR Art 44–49) | P0 |
| Is EU/EEA → Bangladesh a restricted transfer? | n/a | Yes | Yes | Yes — exporter CarbonTally, importer Babui; SCC + TIA required | Legal obligation (GDPR Ch V) | P0 |
| Is Bangladesh adequate for UK? | Not verified as adequate in verified ICO page | n/a | n/a | Cannot rely on adequacy; use UK IDTA / Addendum | Regulatory guidance (ICO) | P0 |
| Is Bangladesh adequate for EU? | n/a | Not verified as adequate in EC page | Not verified as adequate in EC page | Cannot rely on adequacy; use EU SCCs | Regulatory guidance (EC) | P0 |
| Required UK transfer assessment | Transfer risk assessment / data protection test (ICO) | n/a | n/a | Document destination law, government access, supplementary measures | Legal obligation (UK GDPR Art 46) | P0 |
| Required EU transfer assessment | n/a | TIA (EDPB 01/2020) | TIA (EDPB 01/2020) | Bangladesh destination law / practice, enforceability, supplementary measures | Legal obligation (GDPR Art 46) + regulatory guidance (EDPB) | P0 |
| Customer authorization needed? | Yes (subprocessor authorization + objection) | Yes | Yes | Customer must authorize / be informed of Bangladesh use | Contractual / product policy | P0 |
| Customer can opt out? | Yes (recommended) | Yes (recommended) | Yes (recommended) | Implementable per contract; enforce server-side | Contractual / product policy | P0 |
| Subprocessor agreement required? | Yes (UK GDPR Art 28) | Yes (GDPR Art 28) | Yes (GDPR Art 28) | Contract with instructions, security, audit, deletion, transfer terms | Legal obligation | P0 |
| Special-category data allowed? | Prohibit from Bangladesh by default; allow only with explicit approval + enhanced controls | Same | Same | Default prohibition; product policy | Legal (if applicable) + product / security | P0 |
| NHS / financial customer flow-down? | Likely procurement / contract requirements | Likely procurement / contract | Likely procurement / contract | Must verify per tender; not a universal legal mandate | Contractual / procurement | P1 |
| AI vs human processing separation? | Required | Required | Required | Use different mechanism, contract, assessment, disclosure | Product / legal / contract | P0 |

---

## 4. Required Control Matrix

| Control | Legal? | Contract? | Operational? | Security? | Product Policy? | Required Before First Customer? | Required Before Bangladesh Processing? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DPA / subprocessor agreement with Bangladesh entity | Yes (Art 28) | Yes | Yes | — | Yes | Yes | Yes |
| UK IDTA / UK Addendum or EU SCC executed | Yes (UK GDPR / GDPR Art 46) | Yes | — | — | — | — | Yes |
| Transfer risk assessment / TIA | Yes | Yes | — | — | — | — | Yes |
| Customer subprocessor disclosure + authorization | — | Yes | — | — | Yes | Yes | Yes |
| Customer objection / opt-out mechanism | — | Yes | — | — | Yes | Yes | Yes |
| Server-side destination-deny on assignment | — | — | Yes | Yes | Yes | Yes | Yes |
| Server-side assignment-match (`entity_id` = staff `entity_id`) | — | — | Yes | Yes | Yes | Yes | Yes |
| Document gateway: signed URLs only, no public URL | — | — | — | Yes | Yes | Yes | Yes |
| Entity-scoped RLS (`is_entity_member`) verified by negative tests | — | — | Yes | Yes | Yes | Yes | Yes |
| Controlled workspace: no download / print / local copy | — | — | Yes | Yes | Yes | — | Yes |
| Mediated clarification only (no direct entity ↔ customer contact) | — | Yes | Yes | — | Yes | — | Yes |
| Validation / review / QC as CarbonTally-internal gates only | — | Yes | Yes | Yes | Yes | Yes | Yes |
| Named worker accounts; MFA | — | Yes | Yes | Yes | Yes | Yes | Yes |
| Confidentiality, training, access review, rapid revocation | — | Yes | Yes | Yes | — | Yes | Yes |
| Audit trail of assignment / reassignment, scope, actor, reason | — | — | Yes | Yes | Yes | Yes | Yes |
| Evidence preservation (D33 source link, calculation snapshot) | Yes (accountability) | Yes | Yes | — | Yes | Yes | Yes |
| Deletion / return on completion or termination | Yes (Art 28) | Yes | Yes | Yes | Yes | Yes | Yes |
| Incident notification without undue delay | Yes (Art 33) | Yes | Yes | Yes | — | Yes | Yes |
| Government-access notification clause | — | Yes | Yes | — | — | — | Yes |
| Onward-transfer restriction | Yes (Art 28) | Yes | Yes | — | — | — | Yes |
| Periodic reassessment; reassignment / replacement rights | — | Yes | Yes | — | — | — | Yes |
| Verified region / backup / support location | — | — | Yes | Yes | Yes | Yes | Yes (for any residency claim) |
| Disallow special-category data from Bangladesh by default | — | Yes | Yes | Yes | Yes | — | Yes |
| Customer choice (UK-only, EEA-only, no Bangladesh, etc.) | — | — | — | — | Yes | Recommended | Recommended |
| Separate AI provider assessment + contract | Yes | Yes | Yes | Yes | Yes | Yes | n/a (if AI not used) |

---

## 5. Required Operating Model Comparison

| Model | Legal structure | Transfer structure | Customer control | CarbonTally responsibility | Complexity | Recommended? |
| --- | --- | --- | --- | --- | --- | --- |
| A — Subprocessor (CarbonTally contracts Processing Entity) | CarbonTally processor for customer; Processing Entity is subprocessor | Single transfer CarbonTally → entity; one mechanism; one assessment; customer disclosure | Medium (subprocessor notice + objection + agreement) | Highest (assignment, security, evidence, correction, deletion, breach, audit) | Moderate | Yes — recommended |
| B — Customer-approved named subprocessor | Customer explicitly approves entity; CarbonTally still manages process | Same mechanism, customer sign-off; stronger transparency | Higher (customer must approve / authorize / review) | High (same as A, plus customer-consent tracking) | Higher | Possible for enterprise / regulated customers |
| C — Customer contracts directly with Processing Entity | Customer processor; entity subprocessor; CarbonTally own role limited | Potential dual transfer assessments; risk of missing one path | Highest customer control; highest operational complexity | Fragmented (entity reports to customer, not only to CarbonTally) | Highest | Not recommended |

---

## 6. Terminology (as required)

- **Processing Entity**: CarbonTally architectural term (ADR-V3-001, `processing_entities`, Master v1 §312). Use this term, not "processing company" or "outsourcing company", when referring to the CarbonTally model.
- **Processing Entity Staff**: staff members with `entity_id` set; access scoped to assigned entity work only; no customer-organisation membership.
- **Customer Organisation**: `organizations` tenant; data owner.
- **Processing Work**: `manual_extraction_batches` + `manual_extraction_items`; assigned by CarbonTally staff; entity-scoped via `entity_id`; validated, reviewed, QC'd by CarbonTally internal staff; evidence linked via D33.
- **Human Processing**: entity staff performing assigned extraction / mapping; distinct from AI-assisted extraction.
- **Human Review / QC**: CarbonTally staff gates (reviewer / qc_specialist / admin), not entity staff.
- **Evidence**: `calculation_snapshots` (immutable; source_file / source_item_id D33; content_hash; algorithm_version); `emissions_logs`; audit / domain events; source-file linkage; customer review / approval.

---

## 7. Legal Classification of Processing Entity

| Classification | When applicable | Evidence / contract needed | Risk |
| --- | --- | --- | --- |
| Subprocessor | CarbonTally is processor for customer; Processing Entity performs processing on CarbonTally's instructions; contract and subprocessor authorization exist | Subprocessor DPA + customer authorization + transfer mechanism + safeguards | Lowest (clear chain, customer awareness, flow-down obligations) |
| Another processor (not subprocessor) | CarbonTally delegates processing to a separate processor with direct instructions from customer, or customer authorizes another processor beside CarbonTally | Customer authorization + direct instructions + separate processor terms | Medium (more contracts; unclear liability split if both process independently) |
| Independent controller (for its own operations) | Entity decides purposes / means for its own staff management, reporting, billing — not for customer document processing | Separate entity controller determination; must not apply to assigned customer work | Low for own operations; high if applied incorrectly to customer processing |
| Separate service provider | Contract describes only a service to CarbonTally, not processing of personal data; but if document content is accessed, it is still processing | Service contract + data-handling addendum; do not assume "service" avoids GDPR if personal data is accessed | Medium (risk of understatement) |

**Recommended for CarbonTally Human Processing:** **Model A (subprocessor)** for assigned Processing Work, with customer disclosure / authorization where required by contract or procurement, and with CarbonTally remaining responsible for instructions, security, transfer, accuracy, and evidence.

---

## 8. UK Customer Organisation → Bangladesh Processing Entity

### 8.1 Is this an international transfer?

**Yes, when the three conditions are met:** (1) personal data of a UK customer is (2) made available to (3) a separate organization outside the UK for processing.

- The customer's source documents contain business / personal information (supplier names, staff, financial amounts, facility data, sometimes identity or health-related content).
- CarbonTally (or the customer, if direct) makes the work item and associated document available to Babui staff.
- Babui is a company in Bangladesh, a country outside the UK; access is to a separate legal entity.

**Not automatic if** the data is fully anonymised / non-personal (unlikely for business invoices containing supplier / employee / financial info), or access is only by CarbonTally internal staff in the UK, or access is purely for internal CarbonTally operations with no Bangladeshi staff involvement.

**Primary source:** ICO international transfers hub (`https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/`); adequacy regulations (`https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/adequacy-regulations/`); appropriate safeguards (`https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/appropriate-safeguards/`); transfer test (`https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/completing-a-transfer-risk-assessment/`). All verified live.

### 8.2 Exporter / importer / mechanism

| Role | Likely identification | Basis |
| --- | --- | --- |
| Data exporter | CarbonTally UK (processor acting on customer instructions; makes work available to subprocessor) | UK GDPR Art 28 + contract; transfer applies when controller / processor makes data available to recipient |
| Recipient / importer | Babui Limited (Bangladesh) — the Processing Entity performing assigned Human Processing | Actual processing party; separate company; work-assigned access |
| Mechanism (most practical) | UK IDTA or UK Addendum (Art 46(2)(c)/(d)); check whether UK adequacy applies first | ICO safeguards guidance; if Bangladesh is not adequate, IDTA / Addendum is the standard route |
| Assessment required | UK transfer risk assessment / data protection test when using safeguards | ICO transfer-test guidance; must assess destination-country law / practice and whether supplementary measures are needed |

### 8.3 Is UK IDTA the right mechanism?

**Likely yes** for processor → subprocessor or controller → processor transfer of UK personal data to a non-adequate destination, where SCC-style obligations are needed and no adequacy applies.

**When UK Addendum applies:** to supplement EU SCCs when an EU SCC contract already exists and UK-specific terms must be added. If CarbonTally starts with UK contracts only, **UK IDTA** is typically the direct route.

**Requires legal counsel confirmation** on: which exact UK GDPR Art 46 route; whether a UK Extension to EU-US framework applies (not relevant here except for AI comparison); whether any bilateral or sector agreement applies; and whether the specific data categories or volume change the assessment.

### 8.4 Supplementary measures (realistically useful for Human Processing)

Per EDPB Recommendations 01/2020 and ICO safeguards guidance:

- Technical: encryption in transit / at rest; access controls; least privilege; workspace isolation; no direct Storage credentials; short-lived signed access; logging; no local storage / download / print; pseudonymisation / minimisation where possible; restricted document fields.
- Organisational: staff confidentiality; training; policies; audits; incident response; access review; supervision; background checks where lawful / appropriate; termination / revocation.
- Contractual: instructions; purpose limitation; deletion / return; audit rights; breach notification; onward-transfer restriction; government-access notification where appropriate; subprocessor authorization.
- Assessment: destination-country government-access, surveillance, and legal-override analysis for Bangladesh; evaluation of whether supplementary measures can achieve substantially the same protection; if they cannot, suspension.

**Important:** supplementary measures reduce but do not eliminate risk; they must be assessed specifically for the work type (document extraction with potential financial / employee / identity content) and not treated as a checkbox.

---

## 9. Irish / EU/EEA Customer Organisation → Bangladesh Processing Entity

### 9.1 Is this a restricted transfer?

**Yes**, when an EU/EEA controller or processor makes personal data available to an importer outside the EEA, unless an EU adequacy decision covers the destination or a valid Chapter V tool applies.

- The European Commission adequacy decisions page (`https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en`) confirms adequacy is country-specific; no evidence that Bangladesh is listed.
- EU SCCs (`https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en`) are a standard Chapter V safeguard, not an automatic permit — must be accompanied by assessment and supplementary measures.

### 9.2 Exporter / importer / SCC module

| Role | Identification |
| --- | --- |
| Exporter | CarbonTally (if processor) or Customer Organisation (if controlling / directing) |
| Importer | Babui Limited (Bangladesh) |
| SCC module | Module 2 (processor → processor) if CarbonTally is processor for customer; Module 3 (processor → controller) only if Babui independently determines purposes / means for customer work — not the intended model |

### 9.3 Transfer Impact Assessment (TIA)

**Required.** Per EDPB Recommendations 01/2020 and DPC Chapter V guidance. Must assess:

- Bangladesh law / practice relevant to government access, disclosure obligations, and surveillance (authoritative Bangladesh legal sources not fully verified in this research);
- whether SCC contractual terms are enforceable in Bangladesh (requires Bangladeshi counsel);
- whether supplementary technical / organisational measures reduce risk sufficiently;
- whether any risk remains that requires suspension or additional customer disclosure.

**Requires legal counsel confirmation** on Bangladesh-specific assessment; do not assume a standard SCC package eliminates risk.

---

## 10. Ireland — Specific Analysis

### 10.1 Does Ireland introduce additional statutory requirements?

**No additional statute-specific data-residency or processing rule was found** beyond EU GDPR + Irish Data Protection Act + DPC guidance.

- The Irish DPC international-transfer summary (`https://www.dataprotection.ie/en/organisations/international-transfers/transfers-personal-data-third-countries-or-international-organisations`) confirms Chapter V applies, with adequacy, SCCs, BCRs, codes of conduct, and supplementary measures — not a separate Irish-only mechanism.
- HSE requirements must come from the applicable procurement / contract, not from the HSE public site (pages not fully retrieved); this should be documented as a contract / procurement matter, not invented as a legal mandate.

### 10.2 Practical difference from other EU/EEA

Ireland may be relevant because:

- Irish customers often expect EU / European data handling because of sector / regulatory culture, not because of a unique legal rule.
- Irish DPC is active on international-transfer assessments and may ask for evidence if a complaint arises.
- SEAI / IE emission-factor support exists, but factor support is not equivalent to a privacy-law exemption.

---

## 11. Bangladesh Legal / Regulatory Environment

### 11.1 What authoritative sources confirm

- The official `bdlaws.minlaw.gov.bd` index page is live (`http://bdlaws.minlaw.gov.bd/`) and lists statutes by alphabetical / chronological order; keyword searches for "Data Protection", "Personal Data", "Cyber Security", "Cyber Security Act", "Digital Security", "Information and Communication Technology", and "Telecommunication" returned no hits from the parsed index in this session.
- Bangladeshi government portals (`cabinet.gov.bd`, `ictd.gov.bd`, `dpp.gov.bd`) were reachable; `ictd.gov.bd` page loaded; specific data-protection or cyber-security law pages could not be confirmed.
- No authoritative source retrieved in this session confirms a specific enforceable Bangladesh "Personal Data Protection Ordinance 2025" or "Cyber Security Act 2025" text. Search references mention such instruments, but they could refer to drafts, proposed bills, older instruments, or different names / years.

### 11.2 What CarbonTally must do because of this uncertainty

**Do not assume "Bangladesh has no data law" or "Bangladesh law prohibits the transfer."** Both are unsupported by verified sources.

Required actions:

- **Engage Bangladeshi counsel** to confirm whether any Bangladesh statute applies to a service provider processing foreign-personal-data documents remotely; whether the processing is subject to registration, licensing, or reporting; whether local employment / confidentiality / security obligations apply; and whether government-access powers exist.
- **Document the legal opinion** as part of the transfer assessment.
- **Treat any Bangladesh processing until confirmed as "high scrutiny"** — use stricter supplementary measures, enhanced audit, customer disclosure, and suspension rights.
- **Do not claim "Bangladesh complies with local data-protection law"** unless a specific statute and compliance evidence are shown.

### 11.3 Contractual and operational requirements for the Bangladesh Processing Entity regardless of statute status

Even if Bangladesh has no specific data-protection statute applicable to this provider, CarbonTally's UK / EU obligations still require:

- processor / subprocessor contract;
- documented instructions;
- security;
- confidentiality;
- audit;
- deletion / return;
- incident notification;
- onward-transfer restriction;
- government-access notification where relevant.

The contract with Babui must commit to these regardless of local statutory status.

---

## 12. International Transfer Mechanisms (summary)

| Jurisdiction | Potential mechanism | When appropriate | Status / caveat |
| --- | --- | --- | --- |
| UK → Bangladesh | UK IDTA (Art 46(2)(c)) or UK Addendum (if EU SCC base exists) | Non-adequate destination; processor / subprocessor; need enforceable obligations | Requires counsel confirmation; UK assessment required |
| UK → Bangladesh (adequacy only) | UK adequacy regulation | If Bangladesh is later listed; not currently verified | Not verified; do not assume |
| EU → Bangladesh | EU SCC Module 2 (processor → processor) or Module 3 if different role | EU-to-third-country processor flow | Must include TIA and supplementary measures; counsel confirmation needed |
| EU → Bangladesh (adequacy) | EU adequacy decision | If Commission decides Bangladesh adequate | Not verified for Bangladesh |
| All | Exception / derogation (UK GDPR Art 49 / GDPR Art 49) | Only for specific derogations (e.g., consent, contract performance, vital interests, public interest, legal claims) | Not a routine processing route; do not design standard Human Processing around exceptions |

---

## 13. Transfer Risk Assessment / TIA / TRA

### 13.1 What is required

- **UK:** Transfer risk assessment / data protection test (ICO; now called "data protection test" in UK legislation). Must assess whether the destination country's legal framework undermines the SCC / IDTA protections and whether supplementary measures close the gap.
- **EU:** Transfer Impact Assessment (TIA). Must assess the third country's law / practice, whether SCC contractual protections are enforceable, and whether supplementary measures are sufficient.

### 13.2 What must be assessed specifically for Bangladesh Human Processing

- Government-access and disclosure obligations (Bangladesh legal framework uncertain; requires Bangladeshi counsel).
- Whether SCC / IDTA terms are enforceable in Bangladesh (requires local counsel).
- Whether technical / workspace controls (encryption, isolation, no-download, logging, least privilege) reduce the practical risk of unauthorized access or copy.
- Whether any remaining risk requires suspension, additional contract terms, or enhanced monitoring.
- Whether the specific document content (potentially financial / employee / supplier / identity-related) raises the sensitivity level.

### 13.3 What evidence must be retained

- Assessment document.
- Source of assessment (law, guidance, supplier evidence).
- Date and reviewers.
- Destination country and data categories.
- Transfer mechanism and module / version.
- Supplementary measures selected.
- Residual-risk conclusion.
- Review trigger / date.
- Customer acknowledgment / authorization.

---

## 14. Supplementary Measures

Based on EDPB 01/2020 recommendations and ICO safeguards guidance, mapped to CarbonTally's actual Human Processing model:

| Measure type | Control | Risk addressed | Classification |
| --- | --- | --- | --- |
| Technical | Encrypted transmission; encrypted Storage; access via authorized session only | Interception; unauthorized access to documents | Security best practice / contractual |
| Technical | Workspace isolation per assigned work item (D22 `entity_id`; `_entity_checked_item`) | Cross-entity access; access to unrelated customer data | Operational / security |
| Technical | No direct Storage credentials to entity staff; signed URLs with expiry | Uncontrolled storage access; persistent URLs | Technical / contractual |
| Technical | Source-file linkage (D33); calculation provenance; audit trail | Evidence integrity; unauthorized alteration | Product / operational |
| Technical | Redaction / minimisation of non-required fields where possible | Over-collection; unnecessary exposure | Security best practice / product policy |
| Technical | Session expiry; MFA; device / network controls; logging without document text | Credential misuse; session hijacking; log leakage | Security best practice / operational |
| Organisational | Processing Entity contract with instructions, purpose limitation, confidentiality, training | Unlawful / unauthorized purpose; staff error; disclosure | Contractual / legal |
| Organisational | Named worker accounts; no shared accounts; joiner / leaver; periodic review | Uncontrolled access; former staff access | Operational / security |
| Organisational | Supervision; QC (internal staff only; entity staff do not approve) | Incorrect processing; unilateral approval | Operational |
| Organisational | Mediated clarification only; no direct entity ↔ customer contact | Communication leakage; customer privacy breach | Product / operational / legal (design rule) |
| Contractual | Subprocessor authorization; transfer documentation; government-access notification; deletion / return; audit; breach notification; onward-transfer restriction | Subprocessor risk; government access; non-return; audit failure | Contractual / legal |
| Contractual | Customer disclosure of Processing Entity, country, purpose, access, mechanism, security measures | Transparency; authorization; objection | Contractual / legal / product |

**Not sufficient alone:** ISO 27001 claim; "controlled workspace" label; "least privilege" description without enforced assignment-check; "formal arrangement" without executed contract. These are supporting evidence when backed by contracts, assessments, and live controls — not substitutes for the transfer mechanism and assessment.

---

## 15. Processing Entity Contract Requirements

Based on CarbonTally's model (D22, Master v1, Access Model, pricing / assisted specs) and UK / EU processor / subprocessor duties, CarbonTally should contractually require from a Bangladesh Processing Entity at least:

- Legal identity; beneficial ownership where appropriate.
- Contractual purpose: assigned Human Processing only; no independent use of customer data.
- Instructions from CarbonTally; no deviation; documented instructions per batch / item.
- Confidentiality obligations; staff confidentiality; training; access restrictions.
- Security: access control; MFA; device controls; local-copy restrictions; session limits; workspace isolation; logging; incident response.
- Subprocessing: no further subcontracting without CarbonTally authorization; contract terms for any sub-subprocessor.
- Data handling: minimisation; no unnecessary download / print / copy; no unapproved screenshots / photography; deletion / return; retention rules; no retention for training / AI.
- Government access: notification obligations; cooperation; refusal where unlawful (subject to legal advice).
- Audit: right to inspect / design audit; evidence of access / review; periodic reassessment; suspension / replacement rights.
- Incident: breach notification without undue delay; cooperation; evidence preservation.
- Termination: suspension; revocation; deletion / return of incomplete work; deletion of copies; evidence of deletion; exit assistance.
- Transfer / contract: compliance with UK / EU transfer obligations; acknowledgment that UK / EU law may apply; cooperation with assessments.
- Evidence: assignment / reassignment history; worker access logs; QC / review results; source-file linkage; calculation proof.

---

## 16. Customer Contract / DPA Requirements

For UK / IE / EU customers where a Processing Entity (including Bangladesh) is used, the customer agreement should clearly address:

- Controller / processor roles.
- Processing instruction scope; permitted Processing Entities; permitted countries / destinations.
- Subprocessor disclosure; authorization; change process; objection right.
- Transfer mechanism; assessment; supplementary measures.
- Security measures; access controls.
- AI-assisted extraction disclosure and opt-out / policy.
- Human processing disclosure; permitted Processing Entities; permitted countries.
- Retention; deletion; export; legal hold.
- Incident notification; breach assistance.
- Audit / inspection; evidence.
- Confidentiality; staff obligations.
- Liability; indemnity; exit.

The customer should not receive an ambiguous "we may use providers" statement when a Bangladesh Processing Entity will actually access source invoices.

---

## 17. Processing Entity Approval Requirements (policy framework)

| Category | Requirement | Classification |
| --- | --- | --- |
| Legal | Legal identity; beneficial ownership; contract; data-protection obligations; transfer documentation | Legal / contractual |
| Security | Physical / end-point security; MFA; access control; logging; device management; workspace isolation; local-storage restrictions | Security best practice / contractual |
| People | Named staff; confidentiality; training; termination; access review; background checks where lawful / appropriate | Operational / contractual |
| Operations | Assignment only; segregation; QC; clarification mediation; deletion; business continuity | Operational / product |
| Assurance | Security questionnaire; evidence; certifications (scope verified); audit rights; periodic reassessment | Contract / best practice / enterprise |

No item here is automatically "all required by UK GDPR" by itself; together they form a defensible package for an external Human Processing arrangement.

---

## 18. Processing Entity Staff Requirements

| Requirement | Classification | Evidence needed |
| --- | --- | --- |
| Named account; no shared account | Security / operational | User directory; assignment-match check |
| MFA | Security | Authentication log; policy |
| Work assignment match (`entity_id` = staff `entity_id`) | Operational / legal (instructions) | Assignment record; RLS check |
| Confidentiality agreement | Contractual / legal | Signed agreement; staff record |
| Training (privacy / security / workflow) | Operational / contractual | Training record |
| Least privilege (only assigned item / document / fields) | Security / operational | Access log; workspace restriction |
| No customer communication; no direct customer access | Design / legal (communication boundary) | Design rule; API guard; audit |
| Session expiry; device / network controls | Security | Policy; log |
| No unapproved download / print / screenshots | Security / operational | Workspace controls; policy |
| Access review + rapid revocation | Operational | Periodic review; termination process |
| Incident reporting | Contractual / legal | Contract clause; notification log |

---

## 19. Human Processing Operational Policy (required controls by step)

Conceptual flow mapped to CarbonTally terms:

```
Customer Organisation
  → Processing Work (manual_extraction_batches + items, org-scoped)
  → CarbonTally assignment (internal staff only; entity_id OR assigned_to)
  → Processing Entity (only assigned batches / items; never unrelated customer / org data)
  → Processing Entity Staff (entity-scoped; extraction / mapping only; never validation / review / QC)
  → Human Processing (assigned document + fields; workspace isolation)
  → Validation / Human Review / QC (CarbonTally staff gates only)
  → Evidence (calculation_snapshots + audit + source_file link D33)
  → Reporting / Export (org-scoped; customer-approved)
```

Controls at each step:

1. **Assignment gate:** Customer policy permits entity + country; entity active; transfer mechanism active; supplier approved; work item assigned specifically.
2. **Access gate:** Entity staff access only assigned batch / item via `_entity_checked_item`; no org-wide access; documentation / fields restricted to work needs.
3. **Workspace gate:** Controlled viewer; no direct Storage; no download / print; signed URL only; session limited; device / network controlled; logging without document content.
4. **Processing gate:** Extraction / mapping only; validation / review / QC by CarbonTally staff; clarification only through CarbonTally mediation (`entity_extraction_clarify`).
5. **Evidence gate:** Source-file link preserved; calculation provenance preserved; method / actor / provider / version preserved; no silent approval of incomplete or failed work.
6. **Exit gate:** Completed / reassigned / deleted; signed URLs expire; temporary copies removed; deletion evidence; audit preserved.

---

## 20. Special-Category / High-Risk Data

| Category | Recommendation | Classification | Reason |
| --- | --- | --- | --- |
| Health-related data in source documents | Require explicit customer approval + enhanced assessment + stricter supplementary measures + restricted entity / scope | Product / contractual / legal if applicable | Higher sensitivity; potential special-category status; lower tolerance for third-country access |
| Special-category / identity / employee / financial / supplier-confidential | Prohibit from Bangladesh Processing Entity by default; allow only with explicit customer approval + enhanced controls + documented justification | Product policy / security | Not automatically prohibited by UK / EU GDPR alone, but customer risk, sector rules, and confidentiality expectations make it impractical as routine |
| Children's data | Prohibit from external Human Processing unless specifically required, approved, and assessed | Legal / product / security | Higher regulatory and practical sensitivity |
| No special-category / low-risk business data | Permitted with standard safeguards, contract, assessment, and customer disclosure | Legal / contractual / operational | Actual risk depends on content, volume, and document type — not on "business document" label alone |

---

## 21. NHS / HSE / Financial Services

| Sector | Impact on Bangladesh Processing | Source status | Recommendation |
| --- | --- | --- | --- |
| UK NHS | No blanket UK-only legal rule confirmed. DSP ToolKit (`https://www.dsptoolkit.nhs.uk/`) exists; applicable NHS procurement / contract terms determine any data-location / workforce / access requirements. Health-related documents increase sensitivity. | Verified portal; sector contract not reviewed | Treat as procurement / contract matter; require applicable NHS customer contract + DSP / DTAC evidence; do not claim NHS approval without assessment |
| Irish HSE | No additional statutory data-residency rule beyond EU GDPR / Irish Data Protection Act found; HSE requirements come from applicable contract / procurement. | HSE public pages unavailable; no source-established mandate | Confirm with HSE / contract; do not invent Ireland-only rule |
| Financial services (FCA / PRA flow-down) | Customer may require outsourcing evidence (FG16/5 / SS1/21 references standard but pages not fully retrieved); not an automatic CarbonTally obligation. Customer's contract may impose audit, location, subprocessor, resilience, and exit terms. | Source pages not fully retrieved; treat as customer-flow-down | Offer supplier-assurance pack; do not claim financial-regulatory approval without customer-specific review |

---

## 22. AI Provider Comparison (separate from Human Processing)

| Dimension | External AI provider (US / EU / other) | Bangladesh Human Processing (Babui) |
| --- | --- | --- |
| Transfer mechanism | Same UK / EU SCC / IDTA / assessment framework | Same UK IDTA / UK Addendum / EU SCC + TIA |
| Subprocessor status | Subprocessor (if CarbonTally uses it for customer documents) | Subprocessor (if assigned by CarbonTally) |
| Data sent | Document text / fields / prompts; outputs | Assigned source-file content + fields; extraction / mapping output |
| Contract need | AI-provider DPA; region / retention / no-training terms | Processing-entity DPA + worker controls |
| Customer disclosure | Should disclose AI use; offer opt-out / policy | Should disclose Processing Entity, country, purpose; offer objection / choice where contract requires |
| Supplementary measures | Encryption; minimisation; output validation; audit; provider policy | Workspace isolation; least-privilege work-item access; no-download / DLP; mediation; audit |
| Risk profile | Model-training / retention / abuse / support / legal-request risk; prompt injection; incorrect output | Human-copy / photography / download; remote-access device security; government-access; worker error; incorrect result |
| Legal conclusion | Possible with mechanism + contract + assessment + disclosure; US endpoint not automatically prohibited | Possible with mechanism + contract + assessment + safeguards; not automatic; not prohibited; requires approved design |

---

## 23. Recommended CarbonTally Operating Model

**Model A + policy framework + customer choice:**

- CarbonTally UK owns and operates the platform; CarbonTally controls assignment; Processing Entity is a subprocessor for Human Processing on assigned work only.
- Customer agreement discloses Processing Entities, countries, purposes, and access types; includes subprocessor authorization / objection / change process.
- Customer can select (or prohibit): UK-only; EEA-only; no external Human Processing; no external AI; approved named entities only; standard or enterprise terms.
- Each Processing Entity has an approval pack (identity, contract, security, staff, audit, transfer documentation, assessment, supplementary measures, deletion / return, suspension / replacement rights).
- Work assignment uses existing D22 mechanism (`entity_id` XOR `assigned_to` at batch level; entity staff access limited to assigned batches / items via RLS + server-side guard); validation / review / QC remain CarbonTally internal; clarification is mediated.
- External AI, if used, uses separate gateway / policy and is not combined with Bangladesh Human Processing in assessments.
- For UK / IE / EU customers with business / sensitive data, default to **CarbonTally-controlled processing only** until separate approvals exist.

---

## 24. Customer Choice / Data-Location Policy (product / policy, not law)

| Choice / policy | Classification | Notes |
| --- | --- | --- |
| UK-only processing option | Product / contract / procurement | Useful for UK customers; must be technically enforced (region + destination deny), not just labeled |
| EEA-only processing option | Product / contract / procurement | Useful for EU / IE customers; same enforcement needed |
| No external Human Processing | Product / contract / security | Simplest for sensitive / high-risk; must be enforceable server-side |
| No external AI | Product / contract / security | Separate from human processing; must not be conflated |
| Named / approved Processing Entities only | Contract / product | Increases transparency; increases administration |
| Customer objection to Bangladesh | Contract / legal / product | Must be honoured; mechanism must be in DPA / subprocessor terms |
| Customer approval of Bangladesh | Contract / product / best practice | Required for use; not assumed by general terms |

**Recommendation:** Make the choice mandatory at onboarding and enforce server-side; do not rely on the UI label alone.

---

## 25. Processing Entity Approval Framework (policy — not software)

Before assigning any UK / IE / EU Processing Work to a Bangladesh Processing Entity, require evidence for:

1. Legal identity + contract + subprocessor authorization.
2. Transfer mechanism active + assessment complete.
3. Supplementary measures implemented and verified.
4. Staff controls operational: named accounts, MFA, confidentiality, training, least privilege, session / revocation.
5. Workspace isolation verified: assigned-only access; no direct Storage credentials; no download / print; logging without document content; mediation only.
6. Customer authorization / disclosure documented; customer objection mechanism operational.
7. Audit / reassignment / deletion / incident / exit / replacement controls verified.
8. Security questionnaire / certification evidence (scope-verified, not generic).
9. Ongoing monitoring: periodic reassessment; reassignment / replacement rights exercised if failure.

---

## 26. International Human Processing Policy

A single policy should cover:

- When an external Processing Entity is permitted (approved, contracted, assessed, authorized).
- Which countries are permitted per customer profile.
- Which data categories are permitted / restricted.
- Which work types (extraction / mapping vs validation / review / QC) are permitted (entity staff never validate / review / QC per D22 / design).
- Assignment / gate rules.
- Workspace controls.
- Logging / monitoring.
- Incident / replacement / deletion.
- Customer notification / objection / change.
- Evidence retention.

Do not combine AI-provider and Bangladesh-human-processing assessments; they have different risks and different suppliers.

---

## 27. Launch Requirements

### 27.1 Gate 1 — First UK / IE / EU Customer

Before first production customer with personal data: controller / processor register; privacy notice; lawful basis; rights / erasure; DPIA decision; subprocessor list; live tenant isolation; legacy public paths closed; retention / deletion; incident response; verified region / backup / support; customer DPA. (Already required by the prior audit.)

### 27.2 Gate 2 — Bangladesh Processing Entity

Before assigning UK / IE / EU Processing Work to a Bangladesh Processing Entity:

- **Legal:** Entity contract; subprocessor authorization; UK IDTA / UK Addendum or EU SCC + module selection; UK assessment / EU TIA complete; Bangladeshi counsel opinion; supplementary measures selected; customer authorization / disclosure.
- **Transfer:** Exporter / importer documented; mechanism chosen; assessment completed; supplementary measures implemented; residual-risk conclusion documented.
- **Contract:** Processing-entity DPA with instructions, confidentiality, security, audit, deletion, incident, government-access notification, onward-transfer restriction, substitution / replacement rights.
- **Due diligence:** Entity identity; ownership; security; staff; access; workspace; devices; logging; business continuity; incident history; audit rights.
- **Staff:** Named accounts; no shared accounts; MFA; confidentiality; training; least privilege; assignment-match; session / revocation; access review.
- **Operational:** Assignment only via D22 with active entity and customer authorization; workspace isolation verified; mediated clarification only; validation / review / QC by CarbonTally internal staff only; audit trail preserved.
- **Customer:** Explicit authorization for Bangladesh use; disclosure of country / purpose / access / security; objection / change process; no silent assignment to Bangladesh.
- **Documentation:** Transfer register entry; assessment document; contract; supplier evidence; customer acknowledgment; ongoing monitoring plan.

Until Gate 2 is complete, safe default: **UK / IE / EU customer → CarbonTally-controlled processing; no external AI; no Processing Entity outside UK / EEA.**

---

## 28. Enterprise Customer Requirements

Enterprise / regulatory / procurement customers (NHS, HSE, finance, other regulated) may require:

- Verified UK / EEA region profile (database / Storage / backups / support).
- Named subprocessor list with change notice and approval rights.
- No Bangladesh access, or only with customer-specific approval and enhanced controls.
- DSP / DTAC or equivalent evidence.
- Cyber Essentials Plus / ISO 27001 / SOC / pen-test evidence if genuinely held.
- RTO / RPO evidence and restore tests.
- Audit / inspection rights; access logs; privileged-access review.
- Exit / deletion / portability with proof.
- Incident SLAs; breach notification; cooperation.
- Contractual liability / indemnity; concentration-risk management.

These should be treated as **customer-specific contractual / procurement requirements**, not as universal UK / EU legal obligations — unless the specific contract or regulation says otherwise.

---

## 29. Risks / Limitations

- **Bangladesh statutory uncertainty:** No authoritative statute text was verified; must be confirmed by Bangladeshi counsel. Do not assume "no law" or "law prohibits."
- **Live environment unverified:** Transfer assessment applies to actual deployment; code / architecture alone does not prove the live security / region / subprocessor state.
- **Legacy routes unverified as disabled:** Public-URL paths still exist in code; must be disabled and tested.
- **AI and human processing must stay separate:** Transfer / subprocessor assessments must not combine them.
- **ISO 27001 claim:** Must be verified for scope, not treated as automatic compliance.
- **No blanket prohibition on US AI providers:** Must not be overstated; correct statement is "customer / sector / contract / transfer-law dependent".

---

## 30. Questions for Privacy Counsel

1. For UK transfers to Bangladesh: is UK IDTA / UK Addendum the correct Art 46 route, and what exact assessment and supplementary measures are required for document-extraction work?
2. For EU / EEA transfers: which SCC module applies, and what TIA and supplementary measures are required given Bangladesh law / practice?
3. Is Bangladeshi counsel required to confirm whether local statutory obligations apply, and whether SCC / IDTA terms are enforceable?
4. What is the correct exporter / importer identification when CarbonTally is processor for the customer and assigns work to Babui?
5. Does the customer require explicit authorization for Bangladeshi access, or is subprocessor notice / objection sufficient under the customer's contract?
6. What should the DPA include for Processing Entities: instructions, security, audit, deletion, government-access notification, substitution rights, liability?
7. Should special-category / high-risk data be prohibited from Bangladesh Human Processing by default?
8. Does the NHS / HSE / financial-customer contract impose any data-location, workforce, subprocessor, audit, or incident requirement that affects the transfer?
9. What evidence must CarbonTally retain to defend the transfer if an ICO / DPC / customer complaint arises?
10. Can CarbonTally lawfully operate the Processing Entity network without customer-by-customer authorization for each entity / country?

---

## 31. Source Register (authoritative and verified)

**Verified live primary sources (26 August 2026):**

- ICO international transfers hub: `https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/` (200)
- ICO adequacy regulations: `https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/adequacy-regulations/` (200)
- ICO appropriate safeguards / UK IDTA / Addendum: `https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/appropriate-safeguards/` (200)
- ICO transfer test / data protection test: `https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/completing-a-transfer-risk-assessment/` (200)
- ICO DPIA: `https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/` (200)
- ICO security: `https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/security/a-guide-to-data-security/` (200)
- European Commission SCCs: `https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en` (200)
- European Commission adequacy: `https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en` (200)
- EDPB Guidelines 07/2020 controller / processor: `https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-072020-concepts-controller-and-processor-gdpr_en` (200)
- EDPB Recommendations 01/2020 supplementary measures: PDF at `https://www.edpb.europa.eu/system/files_en?file=consultation/edpb_recommendations_202001_supplementarymeasurestransferstools_en.pdf` (200, application/pdf, 1,343,431 bytes)
- Irish DPC international transfers: `https://www.dataprotection.ie/en/organisations/international-transfers/transfers-personal-data-third-countries-or-international-organisations` (200, 49,212 bytes)
- NHS DSP Toolkit: `https://www.dsptoolkit.nhs.uk/` (200, 24,987 bytes)
- UK legislation (Data Protection Act 2018 / GDPR reference): `https://www.legislation.gov.uk/ukpga/2018/12/contents` (200; page content length zero from automated fetch — use as reference citation only, confirm text via official consolidated source)
- EUR-Lex / GDPR: official consolidated text should be used for drafting; not fully retrieved in this session.

**Not fully verified / unavailable (stated as gaps):**

- Bangladesh `bdlaws.minlaw.gov.bd` keyword search returned no hits for data-protection / cyber-security statutes; official index loaded; no authoritative statute text confirmed.
- Bangladeshi government portals (`bgpress.gov.bd`, `legislativediv.gov.bd`, `cabinet.gov.bd`, specific ministry subpages) unavailable or blocked by SSL / network errors.
- UK processor-contract ICO page specific URL returned 404 (hub page available); use hub reference.
- ICO breach-notification and some sector pages unavailable.
- NHS England long-read page unavailable; use DSP Toolkit reference.
- HSE data-protection pages blocked (403) or unavailable.
- FCA FG16/5 and PRA SS1/21 direct URLs blocked; use as sector / customer-flow-down references rather than verified text.

**CarbonTally repository evidence used (read-only; not modified; canonical `d4dcca1`):**

- Term definitions: `docs/architecture/CARBONTALLY_V3_TERMINOLOGY_AND_DOMAIN_GLOSSARY.md`, `docs/architecture/CARBONTALLY_V3_ACTOR_WORKSPACE_ACCESS_MODEL.md`
- Domain model / assignment / isolation / lifecycle / communication / QC: same docs + `docs/architecture/CARBONTALLY_V3_ARCHITECTURAL_DECISIONS_REGISTER.md` + `docs/cline/CarbonTally_Platform_Processing_Architecture_Master_v1.md`
- Implementation: `backend/api/v3_operations.py` (`assign_batch` with `entity_id` XOR `assigned_to`; audit; validation / review / QC gates); `backend/api/v3_manual_extraction.py`; `backend/data/manual_extraction.py`; `backend/domain/entity.py`; migrations V3M-1 / V3M-2 / V3M-6 / D22
- Public claims: `frontend/src/DataSecurity.jsx`; `frontend/src/PricingPage.jsx`; `frontend/src/LandingPage.jsx`
- Previous audit (for continuity): `CARBONTALLY_V3_INDEPENDENT_REGULATORY_AND_DATA_RESIDENCY_AUDIT.md`

---

## 32. Final Decision Answers (explicit)

### 1. Can CarbonTally legally use Bangladesh-based Processing Entities for UK Customer Organisations?

**Yes, conditionally — not automatically prohibited; not automatically permitted.** The transfer is a restricted UK international transfer requiring an appropriate Art 46 mechanism (most practically UK IDTA / UK Addendum if no UK assessment / applicable exception applies), a UK data-protection test / TRA, appropriate contractual / subprocessor controls, supplementary measures, customer disclosure / authorization, and documented evidence. It is not a universal prohibition; it is a regulated arrangement that requires design, contract, assessment, safeguards, and monitoring.

### 2. Can CarbonTally legally use Bangladesh-based Processing Entities for Irish Customer Organisations?

**Yes, conditionally** under the same EU GDPR Chapter V analysis: EU SCC (likely Module 2), EU Transfer Impact Assessment, supplementary measures, customer authorization / disclosure, and documentation. No additional Irish statutory residency rule was found; HSE requirements come from contract / procurement.

### 3. Can CarbonTally legally use Bangladesh-based Processing Entities for other EU/EEA Customer Organisations?

**Yes, conditionally** per EU GDPR Chapter V; adequacy should be checked first; if no adequacy applies, valid SCC / assessment / supplementary measures are required.

### 4. Under what legal structure is this most practical?

**Model A (Processing Entity as CarbonTally's subprocessor)** — clear chain, CarbonTally retains instruction / control / assessment / contract responsibility, customer authorizes / dissents through subprocessor framework. Model B adds customer-specific approval; Model C fragments responsibility.

### 5. What transfer mechanism should CarbonTally consider?

- **UK:** UK IDTA / UK Addendum (primary); UK adequacy only if Bangladesh is listed; exceptions only for specific cases — not standard Human Processing.
- **EU:** EU SCC Module 2 (processor → processor); EU adequacy only if Bangladesh is listed.

### 6. What transfer assessment is required?

- **UK:** UK transfer risk assessment / data protection test (ICO).
- **EU:** EU Transfer Impact Assessment (TIA) per EDPB 01/2020; include destination-country law / practice, enforceability, supplementary measures, residual risk, review trigger.

### 7. What supplementary measures are realistically useful?

Technical: encrypted transmission / storage; isolated workspace per assigned item; signed URL; no direct Storage credentials; least privilege; session / revocation; no download / print; logging without document text; pseudonymisation / minimisation where possible.
Organisational: confidentiality; training; supervision; QC by CarbonTally internal staff; access review; incident response; mediation only; no direct entity ↔ customer communication.
Contractual: instructions; purpose limitation; audit; deletion / return; government-access notification; onward-transfer restriction; substitution / replacement; breach notification; retention rules.
Assessment: destination-country government-access analysis for Bangladesh; confirmation that measures close the gap; suspension if not.

### 8. What must CarbonTally contractually require from a Processing Entity?

Identity, contract, instructions, confidentiality, security, access control, staff controls, mission / assignment-only access, no onward transfer without authorization, deletion / return, audit, breach notification, government-access cooperation, incident cooperation, business continuity, termination / substitution rights, evidence, and transfer-compliance cooperation. ISO 27001 evidence supports assessment but is not a substitute for the contract.

### 9. What must CarbonTally disclose / agree with the Customer Organisation?

Processing Entity name; country; purpose (Human Processing); data categories (business documents possibly containing supplier / employee / financial / identity info); access method (assigned work item, workspace); security measures; AI use (if any); retention; subprocessor authorization / change / objection; transfer mechanism; assessment summary; supplementary measures; customer choice (opt out / approve / country-select); incident cooperation; deletion / export; audit rights. Must not be a generic "service providers" clause.

### 10. Should CarbonTally allow customers to opt out of Bangladesh Processing?

**Yes.** Per contract / procurement best practice and risk management; at minimum for enterprise / regulated / NHS / financial customers; ideally for all. The mechanism should be enforceable server-side, not only UI.

### 11. Should CarbonTally allow customers to select processing destinations?

**Yes — product / policy feature**, where technically enforceable (region / destination deny + assignment gate). Must not be marketed as a legal guarantee unless technically verified for database, Storage, backups, logs, support, AI, email, and human processing.

### 12. Should CarbonTally prohibit certain data categories from Bangladesh Human Processing?

**Yes — by default prohibit special-category / high-risk content (health, identity, sensitive employee / financial, children's) from Bangladesh Human Processing unless explicitly approved by customer + enhanced controls + documented justification.** Not automatically required by UK / EU GDPR for all business invoices, but prudent and defensible given the document content, third-country access, and sector / regulatory expectations.

### 13. Should NHS / HSE customers be treated differently?

**Not by universal legal mandate, but by customer / procurement contract.** NHS customers will likely require DSPT / DTAC-related evidence; HSE customers may have procurement conditions; neither requires "UK-only" or "Ireland-only" by a universal statutory rule. Confirm per tender.

### 14. Should financial-services customers be treated differently?

**By customer contract / regulatory flow-down, yes.** FCA / PRA outsourcing expectations may be imposed by a regulated customer; CarbonTally should provide supplier-assurance evidence but must not claim financial-regulatory approval without customer-specific confirmation.

### 15. What should CarbonTally require before approving a Bangladesh Processing Entity?

Full approval pack (legal identity, contract, security, staff, workspace, transfer documentation, assessment, supplementary measures, audit, substitution / replacement, deletion / return, incident, business continuity, evidence, and periodic reassessment); verified scope of any ISO claim; named-worker controls; assignment-only access; mediation-only communication; no direct customer contact.

### 16. What should CarbonTally require from individual Processing Entity Staff?

Named account; MFA; confidentiality; training; least privilege; assignment-match only; session / revocation; workspace isolation; no download / print; logging without document text; no direct customer communication; access review; supervision; QC by CarbonTally staff only.

### 17. What evidence should CarbonTally retain?

Transfer register; assessment / TIA / TRA; contract / DPA; customer authorization / disclosure; supplier evidence; security questionnaire; staff / assignment logs; workspace-access evidence; audit trail (before → after assignment / reassignment); calculation provenance (D33); source-file links; QC / review records; customer review / approval; deletion / return evidence; incident records; periodic reassessment; review trigger.

### 18. What are the five most important legal / policy actions?

1. Confirm and document the exporter / importer, mechanism, assessment, safeguards, and customer disclosure for Bangladesh Human Processing — not assume prohibition or permission.
2. Execute the Processing-Entity DPA with instructions / confidentiality / security / audit / deletion / transfer terms; get customer authorization; maintain subprocessor register.
3. Do not start Bangladesh Human Processing until the assessment, supplementary measures, workspace controls, staff controls, and customer disclosure are verified — not just "contract signed".
4. Separate AI-provider risk from Bangladesh-human-processing risk; treat both with mechanism / contract / assessment, not with a single "provider" label.
5. Confirm Bangladesh statutory position with Bangladeshi counsel; state the uncertainty in transfer records rather than inventing "no law applies" or "law prohibits."

### 19. What are the five most important operational actions?

1. Enforce assignment-only access server-side (`entity_id` matching; `_entity_checked_item`; RLS `is_entity_member`); never rely on frontend alone.
2. Use controlled workspace (assigned item / document / fields; no direct Storage; signed URLs; session / revocation; DLP; logging without content); verify with negative tests.
3. Keep validation / review / QC as CarbonTally-internal gates; block entity staff from approval / authorization of customer results.
4. Maintain mediated clarification only (`entity_extraction_clarify` → issues → CarbonTally triage → customer-facing surface); never direct entity ↔ customer contact.
5. Monitor / reassess / reassign / revoke; preserve audit; delete when complete; evidence deletion; do not rely on ISO claim alone.

### 20. What should CarbonTally NOT claim publicly without legal confirmation?

- "Bangladesh processing is illegal."
- "UK law requires all data to remain in the UK."
- "EU law requires all data to remain in the EU."
- "NHS requires UK-only data."
- "HSE requires Ireland-only data."
- "GDPR automatically prohibits Bangladesh Processing Entities."
- "No international transfer occurs because data stays in Supabase."
- "ISO 27001 makes Babui fully compliant."
- "US AI providers are prohibited by UK / EU law."
- "All processing is UK-hosted" if backups / support / AI / human access occur elsewhere.

### 21. What should be reviewed by qualified UK / EU / Bangladesh counsel before launch?

- The Processing-Entity DPA terms (instructions, security, audit, deletion, government-access, substitution, transfer).
- The UK IDTA / UK Addendum or EU SCC + module selection and annexes.
- The UK data-protection test / EU TIA and supplementary measures.
- Whether any specific UK / EU / Bangladesh statute or regulatory requirement applies to the specific work type and customer sector.
- Whether ISO 27001 (or other) certification scope covers the relevant Bangladesh operations.
- Whether the customer contract permits the Bangladesh use for the specific document categories.
- Whether specific NHS, HSE, or financial-services requirements apply to the tender.

### 22. What is the most practical legal / operational model for CarbonTally?

**Model A — Processing Entity as CarbonTally's subprocessor**, with documented subprocessor authorization, UK IDTA / EU SCC + assessment, supplementary measures, customer disclosure / objection / opt-out, controlled workspace, mediated clarification, CarbonTally-internal validation / review / QC, audit, deletion / return, incident response, reassignment / replacement rights, and a clear product policy that defaults to CarbonTally-controlled processing for UK / IE / EU customers with sensitive data, with customer choice and destination-deny enforcement server-side.

---

## 33. Safety / Final Checks

- No API keys, passwords, tokens, or credentials reproduced (only "Credential discovered — value not reproduced").
- No source code edited; repository unmodified; isolated clone only used for inspection.
- Every material legal conclusion tied to a verified source or explicitly flagged as unverified / uncertain (Bangladesh statutes; some sector page variants; live region / config not inspected).
- No generic GDPR checklist; all findings mapped to CarbonTally's actual data-flow and architecture terms (Customer Organisation, Processing Entity, Processing Work, Human Processing, Human Review, QC, Evidence, Reporting / Export).
- No assumption that "Processing Entity" equals one legal classification; distinction preserved.

---

## HARD STOP — RESEARCH COMPLETE

Report produced: `CARBONTALLY_V3_BANGLADESH_PROCESSING_ENTITY_LEGAL_POLICY_RESEARCH.md` in the isolated audit workspace.
Not legal advice. Requires confirmation by qualified UK / EU privacy counsel and Bangladeshi counsel before any Bangladesh Processing Entity assignment to UK / IE / EU customer Processing Work.
