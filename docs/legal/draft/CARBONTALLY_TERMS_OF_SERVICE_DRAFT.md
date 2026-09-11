# CarbonTally — Terms of Service (Draft)

**Document status:** DRAFT for review by qualified legal counsel and the Product Owner. Not final. Not legal advice. Not a compliance certification.
**Version:** 0.1 (draft)
**Effective date:** [EFFECTIVE DATE — TO BE INSERTED]
**Last updated:** 24 August 2026 (draft)
**Document owner:** [TO BE ASSIGNED — e.g., CEO / COO with legal counsel]
**Supersedes:** the pre-launch Terms of Service currently shown at `/terms` (`frontend/src/TermsPage.jsx`), once finalised and approved.

> **Drafting note for counsel/PO:** CarbonTally is a pre-launch, pre-payment product. This draft is written so that it remains accurate when billing launches, with clearly marked `[PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL]` items. Statements that depend on product capabilities that do not yet exist are flagged as `[PRODUCT GAP]`. Placeholders for entity details, governing law and jurisdiction are marked `[PLACEHOLDER]`.

---

## 1. About these Terms

1.1 These Terms of Service ("**Terms**") govern the use of the CarbonTally platform and services (the "**Service**") provided by **[PLACEHOLDER: full legal entity name, registered number, registered office, e.g. "CarbonTally Ltd, a company registered in England and Wales, company number [·], registered office [·]" — CONFIRM]** ("**CarbonTally**", "**we**", "**us**", "**our**").

1.2 The Service is a data-processing and emissions-calculation platform that helps organisations convert source activity data (documents and datasets) into structured, validated, calculated and evidenced emissions data, and prepare reporting outputs.

1.3 These Terms apply to the use of the Service, including the public website (`https://carbontally.co.uk`), any authenticated workspace, and any API access made available to you. By creating an account or using the Service you accept these Terms. If you are entering into these Terms on behalf of an organisation, you confirm that you have authority to bind that organisation, and "you" means that organisation.

1.4 Capitalised terms have the meanings given in these Terms or in the Data Processing Agreement ("**DPA**") where defined.

## 2. Pre-launch / current availability

2.1 **Current commercial status:** CarbonTally is preparing for commercial launch. At the date of these Terms, the Service does **not** collect online payments and does **not** offer paid subscriptions through the Service. Access to the Service is provided on a pre-launch, access-by-arrangement basis, and any paid plans, credits or processing orders are indicative commercial features under development (`[PRODUCT GAP — billing/payment integration is not yet operational]`).

2.2 When paid services launch, Sections 12–15 (Fees, Payment, Refunds, Cancellation) will take effect as drafted below, and the then-current pricing page will apply.

## 3. Eligibility and accounts

3.1 You must be at least 18 years old and must not be located in a country that is the target of comprehensive sanctions administered by the UK, EU or US (or applicable law) to use the Service.

3.2 You must provide accurate registration information (including a valid email address) and keep it up to date.

3.3 **Organisation accounts.** The Service is multi-organisation. An account belongs to an organisation and has one or more members with roles (for example owner, admin, member, viewer). The person who creates an organisation is its initial owner. Consultants, Processing Entities and CarbonTally staff operate in separate, role-specific workspaces with separate access rules.

3.4 You are responsible for all activity under your account and for your credentials. You must keep passwords confidential, must not share credentials, and must notify us promptly if you suspect unauthorised use. Authentication is provided through Supabase Auth (email/password and, where enabled, Google sign-in).

## 4. Authorised users and user responsibilities

4.1 You must ensure that your authorised users comply with these Terms.

4.2 You are responsible for the accuracy and lawfulness of the data you upload or enter into the Service, and for ensuring you have the rights and consents necessary to provide that data to us for processing.

4.3 You must not:
- use the Service to store or process data that you are not lawfully entitled to process;
- attempt to access another organisation's data, another consultant's or Processing Entity's workspaces, or any area of the Service you are not authorised to access;
- probe, scan or test the vulnerability of the Service (except through a written, authorised security-testing arrangement);
- reverse engineer, decompile or disassemble the Service (except as permitted by law);
- resell, sublicense or provide the Service to third parties without our written consent;
- use the Service to transmit malware or otherwise interfere with its operation;
- use the Service in breach of applicable law, including data protection law and export controls;
- attempt to circumvent authentication, authorisation, row-level security, or storage access controls.

## 5. Acceptable use and customer content

5.1 "**Customer Content**" means documents, data, and information you or your authorised users upload, enter, or otherwise provide to the Service, and any extracted, validated, calculated or reported outputs derived from them within the Service.

5.2 You retain all rights in Customer Content. You grant CarbonTally a non-exclusive, royalty-free licence to use, copy, store and process Customer Content solely to provide, secure, improve and support the Service, and to comply with law. We do not sell Customer Content and do not use it for purposes unrelated to the Service.

5.3 Customer Content may be processed automatically (including OCR and data extraction) and may be reviewed by authorised CarbonTally personnel or, where applicable, an authorised Processing Entity engaged to perform manual processing, in each case under the DPA and only as necessary to provide the Service.

## 6. Intellectual property

6.1 **CarbonTally IP.** The Service, its software, algorithms, emission-factor databases, calculations engine, documentation, and all related technology and content (excluding Customer Content) are owned by or licensed to CarbonTally and are protected by intellectual-property laws. Except as expressly permitted, you may not copy, modify, distribute or create derivative works from CarbonTally IP.

6.2 **Customer IP.** Nothing in these Terms transfers ownership of Customer Content or your intellectual property. You grant only the limited licence in Section 5.2.

6.3 **Feedback.** If you provide suggestions or feedback about the Service, you grant CarbonTally a perpetual, irrevocable, worldwide, royalty-free licence to use it to improve the Service. Feedback that contains Customer Content remains subject to the DPA and this Privacy Policy.

## 7. Third-party services

7.1 The Service depends on third-party infrastructure providers, including Supabase (authentication, database, storage, realtime), Render (backend hosting), Vercel (frontend hosting) and Resend (transactional email). A current register of these providers is maintained in `docs/legal/CARBONTALLY_THIRD_PARTY_PROCESSOR_REGISTER.md` and in the DPA subprocessor schedule.

7.2 **Third-party failures are not CarbonTally failures.** We are not responsible for failures, outages, or degraded performance of third-party infrastructure, the internet, or other factors outside our reasonable control. See Sections 16 and 19.

7.3 We do not currently integrate a third-party payment provider. When we do, payment processing will be governed by the applicable payment-provider terms and our then-current Payment/Refund Policy.

## 8. Service availability and maintenance

8.1 The Service is provided on an "as available" basis. We use reasonable efforts to keep the Service operational but do not guarantee uninterrupted availability. Planned maintenance may require downtime; we will give reasonable notice where practicable.

8.2 We do not promise specific uptime percentages or response times in these Terms. Any availability or support commitments will be set out in a separate service level description or the MSA and will be agreed in writing (`[PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL]`).

## 9. Beta / experimental functionality

9.1 From time to time we may offer features in beta or experimental status. Such features are provided "as is", without the warranties applicable to generally available features, and may be changed, withdrawn or discontinued at any time without notice.

## 10. AI-assisted processing

10.1 **Current state:** CarbonTally's automatic processing pipeline uses deterministic, local document parsing and OCR. As of the date of these Terms, **no third-party artificial-intelligence service receives Customer Content** in the production pipeline. CarbonTally may in future offer AI-assisted extraction or processing features, in which case these Terms and the Privacy Policy and DPA will be updated before those features process Customer Content, and any applicable provider will be added to the subprocessor register.

10.2 Where AI-assisted processing is offered, output may be imperfect and must be reviewed before use where accuracy matters. AI assistance does not constitute independent verification or assurance (see Section 11).

## 11. Emissions-data and reporting limitations

11.1 CarbonTally processes activity data against emission factors and produces calculations and evidence. **CarbonTally does not provide statutory audit, external assurance, independent verification, or a guarantee of regulatory compliance.** Nothing in the Service constitutes professional, legal, tax, or accounting advice.

11.2 **"Audit-ready" or "evidence" language means evidence/readiness support, not independent assurance.** CarbonTally preserves provenance (source documents, extraction items, factors, calculation snapshots) so that your auditors, verifiers or regulators can review the evidence trail. CarbonTally does not guarantee that any regulator, auditor or verifier will accept any output.

11.3 Calculation results depend on the accuracy and completeness of the data you provide, the emission factors applied, and the methodologies configured. You are responsible for reviewing and approving outputs before they are relied upon.

## 12. Fees (effective when paid services launch) — [PROPOSED]

12.1 Fees for the Service will be set out on the pricing page in effect at the time you subscribe (`frontend/src/PricingPage.jsx` shows indicative plans). Fees may be quoted in GBP and may include VAT or other taxes as applicable.

12.2 **[PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL]** Fees are payable in advance for the relevant period. Plans provide monthly credit allowances measured against a credit model (for example, documents classified as Simple, Standard, Complex or Exceptional consume 1, 2, 4 or quoted credits per unit). Unused credits do not roll over unless a plan states otherwise.

## 13. Payment (effective when paid services launch) — [PROPOSED]

13.1 **[PRODUCT GAP]** Online payment is not yet available. When payment processing launches, it will be provided through a third-party payment provider, and payment-card details will be handled by that provider, not by CarbonTally.

13.2 **Taxes.** Fees are exclusive of VAT and other taxes unless stated otherwise. You are responsible for taxes where applicable. [Governing-law placeholder — confirm VAT treatment.]

13.3 **Failed payments.** If a payment fails, we may suspend the affected subscription and features after notice. `[PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL]`

## 14. Refunds and cancellation — [PROPOSED]

14.1 Refunds and cancellations are governed by the Refund Policy published at `/refund` when billing launches. Until online payments are available, no monetary refunds can be processed; any credit adjustments are governed by the applicable commercial configuration.

## 15. Suspension and termination

15.1 We may suspend or restrict access to the Service (in whole or in part) where: (a) required by law; (b) we reasonably believe there is a security risk or breach of these Terms; (c) you fail to pay any due fees (once billing launches); or (d) continued operation would breach a third-party provider's terms.

15.2 We may terminate these Terms and close accounts for material breach that is not remedied within [·] days of notice, or immediately for serious breach (including violation of acceptable-use rules or security abuse).

15.3 **Data on termination.** On termination we will make Customer Content available for export in accordance with Section 17 (Data export and deletion) to the extent technically supported by the Service. **Limitation:** the Service does not currently provide full organisation export or deletion tooling (`[PRODUCT GAP]`). Our data-deletion obligations are as set out in the DPA and Privacy Policy.

## 16. Confidentiality and security

16.1 Each party will protect the other's confidential information using reasonable care and will use it only to perform its obligations under these Terms.

16.2 CarbonTally applies security controls including authentication, authorisation, organisation-level isolation, row-level security, private document storage (served only through short-lived signed URLs) and least-privilege access for processing personnel. Security is an ongoing process, and we do not warrant absolute security.

## 17. Data protection, data export and deletion

17.1 The parties' data-protection responsibilities are set out in the DPA, which is incorporated into these Terms by reference. Where CarbonTally processes personal data on your behalf, CarbonTally is a processor; where it processes account, billing and support data about you, CarbonTally is a controller. See the Privacy Policy for controller-side details.

17.2 **Data export.** The Service currently provides limited export of emissions data (CSV and JSON) and document metadata (CSV). Full organisation export is not yet available (`[PRODUCT GAP]`).

17.3 **Data deletion.** Account, organisation and document deletion capabilities are limited. The current retention settings and enforcement are described in the Privacy Policy and the consistency audit. CarbonTally will, at a minimum, comply with applicable data-protection law and the DPA. `[PRODUCT GAP — full deletion tooling required]`

## 18. Warranties and disclaimers

18.1 CarbonTally warrants that it will provide the Service using reasonable skill and care and will use commercially reasonable security measures.

18.2 **Except as expressly set out in these Terms, the Service is provided "as is" and "as available", and CarbonTally disclaims all other warranties, express or implied, including merchantability, fitness for a particular purpose, and non-infringement, to the maximum extent permitted by law.** CarbonTally does not warrant that the Service will be uninterrupted or error-free, that calculations are accurate for every regulatory purpose (see Section 11), or that outputs will be accepted by any auditor or regulator.

## 19. Liability

19.1 **Nothing in these Terms excludes or limits liability that cannot be excluded or limited by law** (including death or personal injury caused by negligence and fraud).

19.2 **Subject to Section 19.1, CarbonTally is not liable for indirect, incidental, special, consequential or punitive damages, or for loss of profits, revenue, data, goodwill or business opportunity**, arising out of or relating to these Terms or the Service, even if advised of the possibility.

19.3 **[PROPOSED — REQUIRES PRODUCT OWNER / LEGAL APPROVAL]** CarbonTally's total aggregate liability under or in connection with these Terms will not exceed the greater of (a) the amounts paid by you to CarbonTally in the 12 months preceding the claim, or (b) **[·]**.

19.4 **Allocation of responsibility.** CarbonTally is responsible for the Service it controls. You are responsible for: the accuracy and lawfulness of Customer Content; your credentials and systems; and your decisions based on Service outputs. Third-party infrastructure providers are responsible for their own services. We are not responsible for internet failures, third-party outages, unsupported file formats, customer-configured information, force majeure events, or loss caused by compromise of your credentials.

## 20. Indemnity

20.1 **[PROPOSED — REQUIRES LEGAL APPROVAL]** You will defend, indemnify and hold harmless CarbonTally and its personnel from claims by third parties arising from (a) your breach of these Terms, (b) Customer Content, or (c) your use of the Service in breach of law, subject to our right to assume defence of the matter.

## 21. Force majeure

21.1 Neither party is liable for failure or delay caused by events outside its reasonable control, including natural disasters, war, terrorism, pandemics, government action, power failures, internet disruptions, or failures of third-party services, to the extent the affected party is unable to perform.

## 22. Governing law and jurisdiction — [PLACEHOLDER — CONFIRM]

22.1 These Terms and any dispute arising from them are governed by the laws of **[PLACEHOLDER: England and Wales — CONFIRM]**.

22.2 The courts of **[PLACEHOLDER: England and Wales — CONFIRM]** have exclusive jurisdiction over any dispute, except that either party may seek injunctive or other equitable relief in any court of competent jurisdiction.

## 23. Changes to these Terms

23.1 We may update these Terms from time to time. For material changes we will give reasonable notice (for example, by email or in-product notice) before they take effect. Continued use after the effective date constitutes acceptance. If you do not accept a material change, you may stop using the Service and, where applicable, cancel.

## 24. Notices

24.1 Notices to CarbonTally: email **[PLACEHOLDER: legal@carbontally.co.uk or hello@carbontally.co.uk — CONFIRM]**. Notices to you will be sent to the email address on your account.

## 25. General

25.1 If any provision is unenforceable, it will be limited or severed to the minimum extent necessary; the rest remains in force.

25.2 These Terms, together with the DPA, Privacy Policy, Cookie Policy and (when published) the Refund Policy and any order form or MSA, constitute the entire agreement between you and CarbonTally.

25.3 Neither party may assign these Terms without the other's consent, except that CarbonTally may assign to an affiliate or in connection with a merger, acquisition or sale of assets. These Terms bind and benefit permitted successors and assigns.

25.4 The sections which by their nature should survive termination do survive, including Intellectual Property, Confidentiality, Liability, Indemnity, Data Protection obligations, and Governing Law.

25.5 No failure to enforce a provision is a waiver of it.

---

## Contact

Questions about these Terms: **[PLACEHOLDER email]**.

---

## Change control

| Version | Date | Change summary | Owner |
|---|---|---|---|
| 0.1 | 2026-08-24 | Draft created from product audit; pre-launch status; billing sections as proposals; gaps flagged | [OpenHands audit draft] |
