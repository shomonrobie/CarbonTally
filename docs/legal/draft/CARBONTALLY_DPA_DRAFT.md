# CarbonTally — Data Processing Agreement (Draft)

**Document status:** DRAFT for review by qualified legal counsel and the Product Owner. Not final. Not legal advice. Not a compliance certification.
**Version:** 0.1 (draft)
**Effective date:** [EFFECTIVE DATE — TO BE INSERTED]
**Last updated:** 24 August 2026 (draft)
**Document owner:** [TO BE ASSIGNED]
**Relationship to other documents:** This DPA is incorporated into the CarbonTally Terms of Service and the Master Service Agreement (MSA). In case of conflict with other agreements, this DPA prevails in relation to the processing of personal data.

> **Drafting note:** CarbonTally's product is multi-role and multi-tenant: customer organisations, consultant firms, consultant clients, Processing Entities and CarbonTally staff all process data in different roles. This DPA therefore does **not** make a single universal controller/processor statement; it distinguishes roles by processing activity, and uses SCC/IDTA modules accordingly. Items requiring confirmation are marked `[LEGAL REVIEW]`. Product capabilities that do not yet exist are marked `[PRODUCT GAP]`.

---

## 1. Definitions and roles

1.1 Terms defined in the EU General Data Protection Regulation (Regulation (EU) 2016/679) ("**EU GDPR**"), the UK GDPR and the UK Data Protection Act 2018 (together "**Data Protection Laws**") have the same meanings here. "Personal data" includes special-category data to the extent lawfully processed.

1.2 **Roles.**
- Where CarbonTally processes Personal Data in Customer Content (documents, datasets, extracted data, emissions data) on the documented instructions of the Customer, CarbonTally acts as **processor** and Customer acts as **controller** (or as processor where Customer itself processes for another controller).
- Where CarbonTally processes account, billing, support or technical data about the Customer's users, CarbonTally acts as **controller** in its own right. That processing is outside the scope of this DPA's processor obligations and is described in the Privacy Policy.
- Where CarbonTally acts as a sub-processor of another controller's data under a consultant or Processing Entity engagement, the relevant upstream agreement governs.

1.3 "**Customer Content**" has the meaning in the Terms of Service and includes documents, datasets, extracted data, emissions data and evidence/reporting data uploaded or generated in the Service.

## 2. Subject matter of the processing

2.1 **Subject matter:** provision of the CarbonTally platform for converting activity/emissions source data into structured, validated, calculated, evidenced emissions data and reporting outputs, including document processing (OCR, extraction, mapping, validation, calculation, review, approval) and associated support.

2.2 **Duration:** from the Effective Date until termination of the underlying agreement, and thereafter until all Personal Data has been deleted or returned in accordance with Section 11.

2.3 **Nature and purpose:** processing of Personal Data contained in Customer Content as necessary to provide the Service, and as further instructed by Customer through the Service's functionality (including uploads, mapping choices, factor approvals, review actions, approvals and exports).

2.4 **Categories of data subjects:** the Customer's staff, contractors, suppliers, customers, and other individuals whose personal data appears in Customer Content (for example names, contact details, vehicle/fuel consumption activity data, and other activity/emissions-related data).

2.5 **Categories of personal data:** identity/contact data, activity and operational data (for example fuel, energy, travel, supply-chain activity data), document content, and any other personal data contained in Customer Content. Special-category data is not intentionally processed; Customer must not upload special-category personal data without separate written arrangement `[LEGAL REVIEW]`.

## 3. Customer's instructions and responsibilities

3.1 Customer instructs CarbonTally to process Personal Data in accordance with this DPA, the underlying agreement, and the lawful instructions Customer gives through the Service's functionality. Processing outside those instructions requires prior written agreement.

3.2 Customer is responsible for the lawfulness of the processing, including having a valid legal basis and (where required) consent or other authorisation to provide the data, and for the accuracy and completeness of Customer Content.

3.3 Customer must not provide data whose processing would infringe Data Protection Laws or the acceptable-use rules in the Terms.

## 4. CarbonTally's obligations as processor

4.1 CarbonTally will process Personal Data only on documented instructions from Customer, unless required to do so by law (in which case CarbonTally will inform Customer unless the law prohibits such notice).

4.2 CarbonTally will ensure that persons authorised to process Personal Data are subject to appropriate confidentiality obligations.

4.3 CarbonTally will implement appropriate technical and organisational measures to secure Personal Data, including (as applicable to the current product): authentication (Supabase Auth), role-based access, organisation-level isolation and row-level security, private document storage served only through short-lived signed URLs, least-privilege access for processing personnel, and restricted messaging boundaries.

4.4 CarbonTally will assist Customer, by appropriate technical and organisational measures, to comply with its obligations to respond to data-subject requests and to comply with its obligations regarding security, breach notification, data protection impact assessments, and consultation with supervisory authorities, taking into account the nature of the processing and the information available to CarbonTally.

4.5 **Compliance records:** CarbonTally maintains audit logs and calculation snapshots relevant to processing; detailed compliance documentation is available to Customer on request where reasonably required to demonstrate compliance.

## 5. Sub-processors

5.1 Customer authorises CarbonTally to engage sub-processors to provide the Service, provided that:
(a) CarbonTally imposes data-protection obligations equivalent to this DPA on each sub-processor;
(b) CarbonTally maintains a current list of sub-processors in Schedule 1 and notifies Customer of any intended addition or replacement (via the register and, where applicable, email) with an opportunity to object;
(c) CarbonTally remains liable to Customer for the acts and omissions of sub-processors.

5.2 **Objection:** Customer may object to a new sub-processor on reasonable data-protection grounds within [·] days of notice. If the parties cannot agree, Customer may terminate the affected Service elements. `[PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL]`

5.3 **[PRODUCT GAP / LEGAL REVIEW]** The current subprocessor register must be completed with (a) the Bangladesh Processing Entity (Babui Limited) once the underlying processing arrangement is contracted and verified, and (b) any future payment provider or AI provider.

## 6. International transfers

6.1 The Service is provided using infrastructure in the United States (Supabase, Render, Vercel, Resend) and manual processing by an entity in Bangladesh. Processing therefore involves restricted transfers of Personal Data from the UK/EEA.

6.2 **Transfer mechanisms.** For transfers of UK personal data, the parties adopt the UK International Data Transfer Addendum (or UK Addendum to the EU SCCs); for EU/EEA personal data, the parties adopt the EU Standard Contractual Clauses (Commission Implementing Decision (EU) 2021/914) with the module appropriate to each role, each as set out in Schedule 2. Transfer risk assessments have been or will be completed and retained. `[LEGAL REVIEW — complete and attach assessments]`

6.3 The parties may rely on applicable adequacy decisions or provider certifications (for example, the EU-US Data Privacy Framework) to the extent they cover the relevant transfers.

6.4 CarbonTally will inform Customer of any inability to comply with this Section 6 that would make continued processing unlawful.

## 7. Security

7.1 CarbonTally will maintain appropriate technical and organisational measures as described in the current Data Security documentation, including measures against unauthorised or unlawful processing, accidental loss, destruction or damage (encryption in transit, access controls, tenant isolation, storage access controls). Schedule 3 summarises the current measures.

7.2 Customer acknowledges that the Service depends on third-party infrastructure and that CarbonTally's security obligations are subject to the security posture of those providers as documented in their own materials.

## 8. Personal data breach

8.1 CarbonTally will notify Customer without undue delay after becoming aware of a Personal Data Breach affecting Customer Personal Data, providing available information and taking reasonable steps to mitigate.

8.2 CarbonTally will assist Customer in notifying the relevant supervisory authority and data subjects where Customer is required to do so, considering the nature of the processing and the information available to CarbonTally.

## 9. Assistance with data-subject rights and DPIAs

9.1 Taking into account the nature of the processing, CarbonTally will assist Customer with data-subject requests by providing access to relevant data and appropriate correction, export or deletion tools. **Current limitation:** self-service export is limited to emissions (CSV/JSON) and documents (CSV), and self-service account/organisation/document deletion is not yet available (`[PRODUCT GAP]`). Assistance will be provided manually where operationally possible pending implementation.

9.2 CarbonTally will assist Customer with data protection impact assessments and prior consultation where required, using available information about the Service and its processing.

## 10. Audits

10.1 CarbonTally will make available, on reasonable request and subject to confidentiality, information necessary to demonstrate compliance with this DPA, and will allow for audits and inspections conducted by Customer or an independent auditor appointed by Customer, no more than once per [·] months, at Customer's cost, and not unreasonably interfering with CarbonTally's operations. Where CarbonTally relies on third-party certifications or provider audits, those may be supplied in lieu of a direct audit.

## 11. Deletion and return

11.1 On termination or expiry of the underlying agreement, or on Customer's written request, CarbonTally will delete or return all Personal Data (at Customer's election, where technically feasible) within [·] days, unless applicable law requires retention. **Current limitation:** automated export/deletion coverage is incomplete (`[PRODUCT GAP]`); the parties will cooperate to give effect to this clause using the export mechanisms available, and a full deletion implementation is planned.

11.2 Calculation snapshots, audit logs and evidence records are append-only for auditability and are not routinely deleted; any retention of such records after termination will be limited to what is required for legal or regulatory purposes and documented. `[LEGAL REVIEW]`

## 12. Government / law-enforcement requests

12.1 If CarbonTally receives a request from a law-enforcement or government authority requiring disclosure of Customer Personal Data, CarbonTally will (where legally permitted) inform Customer before responding, and will not disclose more than required. `[LEGAL REVIEW]`

## 13. Liability

13.1 Liability under this DPA is governed by the liability provisions of the Terms of Service / MSA, subject to any liability that cannot be excluded or limited by Data Protection Laws.

13.2 Each party will be liable for damages caused by processing that breaches this DPA or Data Protection Laws, in line with the allocation in Articles 82 (EU GDPR) / Section 197-198 (UK GDPR).

## 14. General

14.1 If any provision is unenforceable it will be limited or severed; the remainder continues.

14.2 This DPA may be updated by CarbonTally where required by changes in law or provider arrangements, with notice to Customer; material changes will not reduce protections below those in this DPA.

14.3 Governing law: **[PLACEHOLDER — England and Wales]**. Jurisdiction: **[PLACEHOLDER]**.

---

# Schedule 1 — Sub-processors and processors

*Status: derived from the current product audit. **[LEGAL REVIEW]** — verify contracts, retention and transfer documentation before reliance.*

| # | Entity | Role | Purpose | Location | Data processed | Transfer mechanism | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Supabase, Inc. | Processor (infrastructure) | Authentication, PostgreSQL database, Storage (documents), Realtime | US (region configurable; project region to be confirmed `[PRODUCT GAP]`) | All platform data incl. documents, auth credentials/sessions | Supabase DPA incl. EU SCCs 2021/914; region selection | In use |
| 2 | Render, Inc. | Processor (hosting) | Backend API/worker hosting | US | Data processed by backend; logs | Render DPA; EU-US DPF certification | In use |
| 3 | Vercel, Inc. | Processor (hosting) | Frontend hosting/CDN | US | Frontend assets; transit data | Vercel DPA (UK IDTA + EU SCCs) | In use |
| 4 | Resend, Inc. | Processor (email delivery) | Transactional email (invites, discovery, beta, support mail) | US | Recipient addresses, email content | Resend DPA (EU SCCs + UK SCCs) | In use |
| 5 | Babui Limited (Bangladesh) | **Sub-processor (manual processing)** — pending verification | Manual document processing under the Processing Entity model | Bangladesh | Customer documents/items assigned to it | **Not yet verified** — requires subprocessor agreement + UK IDTA/EU SCCs + TIA | **[PRODUCT GAP]** |
| 6 | Future payment provider | Processor | Payment processing | — | Payment data | — | Not yet engaged `[PRODUCT GAP]` |
| 7 | Future AI/LLM provider | Processor/sub-processor | AI-assisted extraction (if enabled) | — | Customer documents (if enabled) | — | Not yet engaged `[PRODUCT GAP]` |

**Notes**
- OCR/parsing (Tesseract, ONNX RapidOCR, pdfplumber, pandas) run locally on CarbonTally's own backend infrastructure and are not third-party processors.
- Each provider's own subprocessors are listed in the provider's official documentation (see the Third-Party Processor Register). Those are not CarbonTally's direct subprocessors but are relevant to transfer analysis.

# Schedule 2 — Transfer mechanisms (to be completed by counsel)

| Transfer | Mechanism | Status |
|---|---|---|
| UK → US (Supabase/Render/Vercel/Resend) | UK IDTA / UK Addendum to EU SCCs; DPF where applicable | To be completed `[LEGAL REVIEW]` |
| EU/EEA → US | EU SCCs 2021/914 (modules by role) | To be completed `[LEGAL REVIEW]` |
| UK/EU → Bangladesh (Babui) | UK IDTA / EU SCCs + transfer risk assessment | To be completed `[LEGAL REVIEW]` |

# Schedule 3 — Technical and organisational measures (current)

1. Authentication via Supabase Auth (email/password, Google OAuth; magic-link flow), sessions and credential management by Supabase.
2. Server-authoritative authorization: organisation membership, role checks, consultant grant checks, Processing Entity scoping; RLS as a defence-in-depth layer.
3. Document storage in a private Supabase bucket; access only through short-lived signed URLs; storage paths are not treated as authorization.
4. Durable, resumable, idempotent processing jobs with persisted state; duplicate-prevention on calculations.
5. Audit logs and append-only calculation snapshots for traceability.
6. Least-privilege access for CarbonTally and Processing Entity personnel; no unrestricted customer↔PE communication.
7. Encryption in transit (HTTPS); signed-URL delivery; no public-link exposure of documents.
8. Deployment: backend on Render, frontend on Vercel, database/auth/storage on Supabase; configuration via environment variables.

---

## Change control

| Version | Date | Change summary | Owner |
|---|---|---|---|
| 0.1 | 2026-08-24 | Draft created from product audit; role-flexible DPA; subprocessor schedule with gaps flagged | [OpenHands audit draft] |
