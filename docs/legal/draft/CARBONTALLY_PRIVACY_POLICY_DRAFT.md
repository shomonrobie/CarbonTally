# CarbonTally — Privacy Policy (Draft)

**Document status:** DRAFT for review by qualified legal counsel and the Product Owner. Not final. Not legal advice. Not a compliance certification (including no GDPR, ISO or SOC certification claim).
**Version:** 0.1 (draft)
**Effective date:** [EFFECTIVE DATE — TO BE INSERTED]
**Last updated:** 24 August 2026 (draft)
**Document owner:** [TO BE ASSIGNED]
**Supersedes:** the pre-launch Privacy Policy at `/privacy` (`frontend/src/PrivacyPolicy.jsx`), once finalised and approved.

> **Drafting note:** This policy describes how CarbonTally actually handles personal data across the public website and the platform, based on the current product audit. Items that require legal confirmation are marked `[LEGAL REVIEW]`. Items that depend on product capabilities that do not yet exist are marked `[PRODUCT GAP]`. This draft is **designed to address relevant data-protection requirements** and requires legal review; it does not assert compliance certification.

---

## 1. Who we are

1.1 CarbonTally provides the CarbonTally carbon data-processing and emissions platform. In this policy "we", "us" and "our" mean **[PLACEHOLDER: CarbonTally Ltd, registered in England and Wales, company number [·], registered office [·] — CONFIRM]**.

1.2 We are a controller of the personal data we collect about you directly (account, contact, billing and support data). Where we process personal data contained in documents and data you upload on your behalf (for example, data about your employees, suppliers or business activities), we act as a **processor** under a Data Processing Agreement (DPA). The DPA governs that processing; this policy explains how we handle data as a controller.

## 2. What this policy covers

This policy explains how personal data is collected and used when you visit our public website (the "site") or use the CarbonTally platform (the "platform") as an authenticated user, consultant, Processing Entity user, or other authorised person.

## 3. Data categories, why we collect them, and legal bases

| Category | Examples | Why we collect / process it | Legal basis (UK GDPR) | Retention |
|---|---|---|---|---|
| Identity & contact data | Name, email address, job role, company/organisation name | To create and administer accounts; to identify you; to contact you | Contract; legitimate interests | Until account closed; then as required by law `[LEGAL REVIEW]` |
| Account & authentication data | Email, password hash, session tokens, OAuth identity, login history | To authenticate you and keep the platform secure (Supabase Auth) | Contract; legitimate interests (security) | Per account lifecycle; auth provider records `[LEGAL REVIEW]` |
| Organisation data | Organisation name, company number, members, roles, metadata, facilities, assets, vehicles, suppliers | To provide the multi-tenant Service and its workspaces | Contract | Life of the account |
| Uploaded documents | PDFs, CSVs, XLSX, images containing activity/emissions source data | To perform processing: extraction, mapping, validation, calculation, evidence, review, reporting | Contract (processing on your instructions) | Retention settings; see Section 8 |
| Extracted & calculated data | Extracted line items, mapped factors, calculation snapshots, emissions results | To deliver the core Service and preserve provenance/evidence | Contract | Life of the account; snapshots are append-only for auditability |
| Communications | Emails to us; in-app messages and notifications | To respond to enquiries and provide support/messaging | Legitimate interests; contract | As needed; messages retained for the account |
| Billing data | Payment records (provider-neutral; no card details stored today) | To manage orders, credits and payments when billing launches | Contract; legal obligation (tax) | Per accounting/tax law `[LEGAL REVIEW]` |
| Technical/usage data | Logs, device/browser data, error data, API usage | To operate, secure and improve the platform | Legitimate interests | Log retention settings; see Section 8 |
| Cookies / browser storage | Auth sessions in browser localStorage | To keep authenticated users signed in | Contract (functionality) | Cleared with browser storage; see Cookie Policy |

**Consent:** We do not currently rely on consent for core platform processing. Where we ever process on the basis of consent (for example, marketing or optional features), we will obtain it separately and you may withdraw it at any time. `[LEGAL REVIEW — confirm each legal basis]`

## 4. How we use information

- To provide, secure, maintain and improve the platform and its workspaces.
- To process documents and datasets on your instructions (extraction, mapping, validation, calculation, evidence, review, approval, reporting).
- To communicate with you about your account, service changes and support.
- To comply with legal obligations and to exercise or defend legal claims.

## 5. Automated decision-making and AI

5.1 **AI in the current product:** CarbonTally's automatic processing pipeline uses deterministic, local parsing and OCR. As of the date of this policy, **no third-party AI service receives documents or extracted data** in the production pipeline.

5.2 Where we introduce AI-assisted processing in future, we will update this policy and the DPA (including subprocessor disclosures and any required transfer safeguards) **before** such processing begins.

5.3 We do not currently use automated decision-making that produces legal or similarly significant effects about you based solely on automated processing. If we ever do, we will provide appropriate information and safeguards. `[LEGAL REVIEW]`

## 6. Sharing and recipients

6.1 We do not sell personal data.

6.2 We share personal data only with:
- **Service providers** that help operate the platform, under appropriate contractual safeguards (see the Third-Party Processor Register and the DPA subprocessor schedule). Current providers: **Supabase** (authentication, database, storage, realtime), **Render** (backend hosting), **Vercel** (frontend hosting), **Resend** (transactional email).
- **Authorised Processing Entities** engaged for manual document processing (currently including **Babui Limited in Bangladesh**), under a formal arrangement and only where work is assigned to that entity. Processing Entity users do not receive unrestricted access to customer data, and there is no direct customer↔entity communication channel. `[LEGAL REVIEW — international transfer safeguards required; see Section 7]`
- **Consultants** you are associated with, within the scope of their authorised access to your organisation.
- **Legal authorities** where required by law or to protect rights/safety. `[LEGAL REVIEW — add lawful-request handling detail]`

6.3 We do not otherwise share personal data with third parties for their own purposes.

## 7. International transfers

7.1 Our service providers (Supabase, Render, Vercel, Resend) are US-headquartered or process data in the United States, and the authorised Processing Entity operates in Bangladesh. Providing the Service to UK/EU/EEA customers therefore involves transfers of personal data outside the UK/EEA.

7.2 Where required, we rely on appropriate safeguards, including **UK International Data Transfer Addendum / EU Standard Contractual Clauses**, supplemented by transfer risk assessments, and provider certifications such as the EU-US Data Privacy Framework where applicable. `[LEGAL REVIEW — confirm current transfer mechanisms and complete assessments]`

7.3 Data residency: the region of our production Supabase project is being confirmed `[PRODUCT GAP — confirm and document]`.

## 8. Retention and deletion

8.1 **Retention is configurable and server-side.** CarbonTally maintains retention settings (e.g., `document_retention_days`, `data_retention_days`, `audit_log_retention_days`, `backup_retention_days`) surfaced at `/api/v3/settings/retention`. **Current enforcement is limited to document retention (soft-delete) and is not automated** (`[PRODUCT GAP]`).

8.2 **Calculation snapshots, audit and evidence data are append-only and are not routinely deleted**, to preserve auditability and evidence provenance.

8.3 **Your rights in practice:** You may request deletion of your personal data (Section 9). **Currently the platform does not provide self-service account or organisation deletion or full data export** (`[PRODUCT GAP]`). Until this is implemented, deletion requests will be handled manually where operationally possible. This limitation is being addressed as a priority.

8.4 We retain personal data only as long as necessary for the purposes in this policy or as required by law, then delete or anonymise it. `[LEGAL REVIEW — align with documented retention schedule]`

## 9. Your rights (UK GDPR / EU GDPR)

You have rights, subject to applicable law and our role (controller vs processor):

- **Access** — obtain a copy of your personal data.
- **Rectification** — correct inaccurate data.
- **Erasure** — request deletion of your personal data. *(Currently limited by the product gaps in Section 8.3.)*
- **Restriction** — restrict processing in certain circumstances.
- **Objection** — object to processing based on legitimate interests or for direct marketing.
- **Portability** — receive your data in a structured, machine-readable format where applicable.
- **Complaint** — lodge a complaint with the UK Information Commissioner's Office (or your local supervisory authority).

To exercise these rights, contact us at **[PLACEHOLDER email]** with proof of identity. Where we process data as a processor for a customer, we will coordinate with that customer (the controller) in line with the DPA. We aim to respond within one month; we may extend by up to two further months for complex requests. `[LEGAL REVIEW — align with DPA DSAR workflow and product capabilities]`

## 10. Security

We apply security controls including authentication (Supabase Auth), role-based access, organisation-level isolation, row-level security, private document storage (served only through short-lived signed URLs), least-privilege access for processing personnel, and controlled processing workflows. See the Data Security page. Security is an ongoing process; no method of transmission or storage is completely secure. `[Data Security page is not currently routed publicly — PRODUCT GAP]`

## 11. Children

The Service is not directed at children under 18, and we do not knowingly collect personal data from them.

## 12. Controller identity and contact

Controller for the personal data described in this policy: **[PLACEHOLDER — CarbonTally Ltd contact details, registered office]**.

Contact for privacy enquiries and data-subject requests: **[PLACEHOLDER email]** .

We have not appointed a DPO because none has been designated. `[LEGAL REVIEW — confirm whether a DPO is required by volume/nature of processing]`

## 13. Changes to this policy

We will update this policy as the product and processing change. Material changes will be notified (for example, by email or in-product notice). The date at the top reflects the latest revision.

## 14. Governing law

This policy and any disputes relating to it are governed by the laws of **[PLACEHOLDER: England and Wales — CONFIRM]**, subject to applicable data-protection law.

---

## Change control

| Version | Date | Change summary | Owner |
|---|---|---|---|
| 0.1 | 2026-08-24 | Draft created from product audit; data categories mapped to actual processing; deletion/AI/transfer gaps flagged | [OpenHands audit draft] |
