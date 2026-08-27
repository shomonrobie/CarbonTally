# CarbonTally V3 Independent Regulatory and Data Residency Audit

**Assessment date:** 24 August 2026  
**Code baseline:** `d4dcca1eb11f86bcae497815c8592d688a7e305f` (`origin/main`)  
**Assessment mode:** Independent, read-only architecture and regulatory audit  
**Scope:** Repository evidence and publicly accessible authoritative guidance only. This is not legal advice, a penetration test, a live Supabase review, or a supplier assurance opinion.

> **Credential discovered — value not reproduced.**

## 1. Executive Summary

CarbonTally is a multi-tenant document-ingestion and emissions-processing platform. Its intended flow is: customer upload → Supabase Storage/PostgreSQL → FastAPI/OCR and deterministic processing → optional LLM extraction → CarbonTally or external human review → validation/QC → immutable calculation/evidence records → reporting/export. The repository implements meaningful tenant and entity concepts, private-document controls in the newer V3 path, signed URLs, RLS migrations, provenance columns, and role/entity tests.

The repository does **not** establish that a production compliance programme exists. The live hosting regions, backup locations, provider contracts, AI provider identity, retention execution, incident runbook, DPIA, transfer assessments, supplier assurance, and customer-facing privacy disclosures were not independently evidenced. Project documents are therefore treated as design intent, not legal evidence.

The most important conclusion is that there is no general UK or EU rule requiring every CarbonTally record to remain in the UK or EEA. UK GDPR and EU GDPR permit international transfers subject to their respective Chapter V regimes. However, a UK/EU customer document made accessible to a separate Bangladesh processing company is ordinarily an international transfer when the three transfer conditions are met; this requires a valid transfer tool, a documented transfer/data-protection test, contractual controls, and technical/organisational safeguards. The same analysis applies to an external AI provider outside the UK/EEA. There is no blanket prohibition on US AI providers; customer contracts, provider terms, transfer law, public-sector procurement, sector regulation, and data sensitivity can still make a US provider unacceptable.

**Release view:** CarbonTally should not accept production personal data from a UK, Irish, or other EU customer until it can identify the controller/processor chain, document purposes and retention, operate tested rights/erasure and incident processes, close the legacy public-URL path, verify live tenant isolation, and evidence all subprocessor and transfer arrangements. External AI and Bangladesh processing should be feature-gated until their provider and transfer control packs are approved.

### Priority meanings

- **P0:** must address before relevant customer data processing.
- **P1:** before commercial launch for relevant customers.
- **P2:** enterprise/regulatory readiness.
- **P3:** future enhancement.

## 2. CarbonTally Data Map

| Stage | Data likely present | Stored/processed/accessed | Transfer/copy/log risk | Control/evidence in baseline |
|---|---|---|---|---|
| Customer account and membership | Names, emails, user IDs, roles, organisation metadata, possibly company identifiers | Supabase Auth plus PostgreSQL tables; FastAPI reads membership and staff records | Auth logs, email/invitation service, support access, backups | Supabase authentication calls; organisation RLS migrations; no live configuration evidence |
| Upload | PDF/image invoices, spreadsheets, filenames, MIME type, dates, energy/financial data, embedded personal data | FastAPI request memory; Supabase Storage `documents`; `organization_files`, `customer_documents`, extraction tables | Browser/API, storage copies, temporary processing memory, failed-upload logs | V3 `/api/v3/uploads` creates org path; legacy `/api/upload-*` remains mounted |
| Storage | Original document bytes and path metadata | Supabase Storage bucket and PostgreSQL metadata | Supabase subprocessor, backups/PITR, signed URL recipients, legacy public URL paths | D32 migration makes `documents` private and adds storage RLS; legacy code still calls `get_public_url` |
| OCR/PDF processing | Full file, rendered page images, OCR text and samples | FastAPI/Python process; local libraries Tesseract, pdf2image, Pillow, pypdf/reportlab | Process memory, stdout/error logs, repaired PDF copy in Storage | Local OCR dependencies; no external OCR transfer evidenced |
| Deterministic extraction/mapping | Supplier, invoice, dates, quantities, units, facilities, factors, emissions | FastAPI and PostgreSQL; JSONB extraction/mapping columns | Audit/domain events, exports, backups | DEFRA/SEAI provider model; tests and calculation snapshots |
| AI extraction (optional design/engine) | Document text, requested fields, extracted values, confidence | Generic `LLMClient` can POST to configured external endpoint | Third-country transfer, provider retention/training, provider abuse monitoring, prompt injection | `backend/infra/llm_client.py` supports arbitrary OpenAI/Anthropic-compatible endpoint; production composition and policy were not found |
| Human processing | Source document, OCR/AI output, customer notes, corrections, staff identity and performance | CarbonTally staff or Processing Entity workspace; entity/work-item tables | Bangladesh or other provider access; screenshots/downloads; remote endpoints; support tools | Entity IDs, entity RLS SELECT policies, work-assignment design; write-path and live provider controls incomplete/unverified |
| Validation/QC/customer approval | Extracted data, evidence, reviewer/QC identity, approval and rejection reasons | PostgreSQL workflow, logs, reports | Human access, notifications, exports, backups | `manual_extraction_items`, review, QC, verification, audit and evidence structures |
| Evidence/calculation | Source item/file/page, factor identity, multiplier, algorithm version, hash, CO2e result | `calculation_snapshots`, `emissions_logs`, domain/audit events | Reports and audit exports; immutable-history expectations | D33 source links and snapshot design; live immutability and retention not verified |
| Reporting/export | Emissions, documents, report versions, possibly customer personal data | FastAPI response, CSV/JSON/PDF, report storage/version tables | Browser downloads, customer systems, email/support, cached files | V3 export routes are org-gated; export history/expiry and download audit are not consistently evidenced |
| Email/notifications | Recipient addresses, document/report status, issue text, links | Resend/SMTP integration and email log tables | Email provider and recipients; email body/link forwarding | `resend` dependency and email logs; DPA, region, retention, minimisation not evidenced |
| Backups/support | Database, Storage objects, logs, audit trails, secrets/configuration | Supabase/provider backups, developer/operator support systems | Backup region, support access, restore copies, ticket attachments | Schema has backup metadata fields; no executable CarbonTally backup/restore policy or location evidence |

**Important distinction:** a storage bucket region, application region, database region, backup region, support-access location, and human worker location are separate facts. A customer-facing “UK hosted” statement cannot be inferred from one of them.

## 3. Controller/Processor Analysis

### Finding CP-1 — Roles are designed but not contractually evidenced

**FINDING:** Likely controller/processor ambiguity across the platform, CarbonTally, customers, human providers, AI providers, email, hosting and support. **EVIDENCE:** The architecture documents call the customer the data owner and a Processing Entity a processor; `processing_entities` and `staff_profiles.entity_id` exist in migrations, while provider contracts, Article 28 terms, subprocessor authorisations and processing instructions are not in the repository. **LEGAL/REGULATORY BASIS:** UK GDPR and EU GDPR distinguish controller and processor by purposes and means; a processor acts on documented controller instructions and the controller remains responsible for its processor chain. See EDPB Guidelines 07/2020 and UK ICO processor-contract guidance hub. **CARBONTALLY IMPACT:** A customer may be controller and CarbonTally processor, but CarbonTally can be an independent controller for account, billing, security, fraud, support or product analytics purposes; a human company and AI provider are normally CarbonTally’s subprocessors where they process customer documents on CarbonTally’s instructions. **CURRENT STATE:** Conceptual role labels exist; actual purposes and contracts are not verified. **GAP:** No authoritative record of purpose-by-purpose roles, instructions, data categories, subprocessor chain, liability, audit, deletion and assistance obligations. **RECOMMENDATION:** Maintain a processing register and signed DPA template per service; record controller/processor determination separately for customer data, CarbonTally operational data, support and billing; require customer authorisation and flow-down terms for every subprocessor. **PRIORITY:** P0.

### Finding CP-2 — Entity isolation is not the same as privacy compliance

**FINDING:** Entity RLS and application scope reduce accidental cross-customer access but do not prove lawful processing, confidentiality, or transfer compliance. **EVIDENCE:** `20260810050000_v3m6_entity_rls.sql` provides entity-scoped SELECT policies; D22 deliberately leaves entity writes service-role/application controlled. **LEGAL/REGULATORY BASIS:** UK GDPR/EU GDPR accountability and security duties require appropriate measures and demonstrable compliance, not merely a database predicate. **CARBONTALLY IMPACT:** An entity worker can still be an authorised recipient in a prohibited or undocumented transfer, and service-role/application bugs can bypass the intended SELECT boundary. **CURRENT STATE:** Strong design intent and unit tests; live-policy tests, privileged-path review, and supplier controls not evidenced. **GAP:** No independent production authorisation matrix and no proof that every legacy route and support path honors it. **RECOMMENDATION:** Treat RLS, API authorization, workspace masking, supplier contract and audit evidence as separate controls; test each role against every data class. **PRIORITY:** P0.

## 4. UK GDPR

### Finding UK-1 — UK applicability and accountability pack are incomplete

**FINDING:** UK GDPR applicability is plausible for CarbonTally’s UK establishment and UK customers, but the repository does not evidence the required accountability artefacts. **EVIDENCE:** UK target-market documents and UK-specific routes/configuration exist; no completed record of processing, privacy notice, lawful-basis matrix, data-subject process, DPO/representative determination, or processor register was found. **LEGAL/REGULATORY BASIS:** UK GDPR applies to processing by a UK establishment and to relevant offering/monitoring activities; the accountability, transparency, processor, security and rights duties then depend on the actual processing. ICO UK GDPR guidance and the Data Protection Act 2018 are authoritative references. **CARBONTALLY IMPACT:** UK customers need a clear controller/processor answer, privacy information and operational rights route. **CURRENT STATE:** Architecture describes tenant and processing flows; legal operating documents are unverified. **GAP:** No evidence package that can be provided to a customer or ICO. **RECOMMENDATION:** Complete the record of processing and privacy notice before onboarding; document lawful bases and special-category determination for each field; provide DSAR, rectification, restriction, objection, portability and erasure runbooks. **PRIORITY:** P0.

### Finding UK-2 — The legacy surface creates a release-blocking data exposure risk

**FINDING:** The newer V3 path uses private Storage and signed URLs, but mounted legacy routes still return or create public URLs. **EVIDENCE:** `backend/services/storage.py` and `backend/api/v3_documents.py` use signed URLs; `backend/routes/upload.py:404-415` calls `get_public_url` for repaired PDFs, and lines 410-415 return it; `backend/routes/organizations/files.py` and legacy customer-document routes also contain public-URL paths. `/api/test-upload` at `backend/routes/upload.py:107-121` is not authenticated and reads uploaded content into a response. **LEGAL/REGULATORY BASIS:** UK GDPR security requires appropriate technical and organisational measures, including confidentiality and resilience; ICO security guidance specifically discusses access control, encryption, processors and restoration. **CARBONTALLY IMPACT:** A public or predictable object URL can disclose customer documents independently of database RLS. **CURRENT STATE:** D32 is a positive V3 hardening, but legacy paths remain reachable through `main.py` router registration. **GAP:** No single enforced document gateway and no evidence that old objects were made private/re-keyed or that all URLs are short-lived. **RECOMMENDATION:** Before production personal data, disable/remove unauthenticated test and legacy public-document routes, make every document response authorization-gated and signed, use org-scoped paths for every generated copy, and verify Storage policy plus CDN/cache behavior in a live test. **PRIORITY:** P0.

## 5. EU GDPR

### Finding EU-1 — Irish/EU use is not automatically blocked, but the EU operating pack is missing

**FINDING:** Ireland/EU onboarding is legally possible without an EU-only storage architecture, subject to GDPR, Irish law, contractual and sector-specific requirements. **EVIDENCE:** The baseline supports `GB`/`IE` factors and an organisation tenant; no EU-specific controller notice, DPC contact/process assessment, EU representative analysis, or transfer register was found. **LEGAL/REGULATORY BASIS:** GDPR Articles 3, 5, 13–14, 28, 32, 35 and Chapter V; the Irish DPC’s international-transfer guidance states that transfers to third countries must comply with Chapter V and may require an adequacy decision, safeguards and supplementary measures. **CARBONTALLY IMPACT:** An Irish customer needs the same core privacy/security controls plus a defensible Irish/EU transfer and supplier position. **CURRENT STATE:** Data model and provider factors are IE-aware; legal controls are not evidenced. **GAP:** No EU/Irish launch evidence pack. **RECOMMENDATION:** Complete EU GDPR mapping, DPC-facing rights and breach procedures, and EU transfer documentation before Irish/EU production data. **PRIORITY:** P0.

### Finding EU-2 — Data location is a design choice, not a GDPR absolute

**FINDING:** No general EU GDPR rule requires all Irish/EU data to stay within the EEA. **EVIDENCE:** European Commission adequacy guidance explains that an adequacy decision permits flows without additional transfer safeguards; Commission SCC guidance describes SCCs for EU-to-third-country transfers. **LEGAL/REGULATORY BASIS:** GDPR Chapter V Articles 44–49. **CARBONTALLY IMPACT:** An EEA region may simplify procurement and risk but does not replace a controller/processor contract, security measures, retention or rights operations. **CURRENT STATE:** Supabase/Render/Vercel locations are not evidenced. **GAP:** Marketing or sales cannot safely infer “EU resident” from the IE factor set or the presence of an Irish customer. **RECOMMENDATION:** Publish only a verified service-by-service location statement, including backups, support and subprocessors; offer regional deployment or exclusion controls where contractually needed. **PRIORITY:** P1.

## 6. International Transfers

### Finding TRANS-1 — Transfer register and assessment are absent

**FINDING:** CarbonTally lacks evidence of a transfer inventory covering storage, hosting, support, email, AI, human processing, backups and remote access. **EVIDENCE:** The repository names Supabase, Render/Vercel-style deployment, Resend and generic LLM endpoints, and explicitly describes Bangladesh processing, but no current transfer register, data-flow approval, UK data protection test/TRA or EU transfer impact assessment was found. **LEGAL/REGULATORY BASIS:** ICO international-transfer hub (updated 2026) separates adequacy regulations, appropriate safeguards and the transfer risk assessment/data protection test; EDPB Recommendations 01/2020 require assessment of third-country law/practice and supplementary measures where needed; DPC Chapter V guidance follows the same framework. **CARBONTALLY IMPACT:** CarbonTally cannot substantiate whether any particular customer’s transfer is lawful. **CURRENT STATE:** High-level diagrams only. **GAP:** No exporter/importer, destination, data category, purpose, volume, tool, assessment, supplementary measure, expiry or review owner. **RECOMMENDATION:** Create a transfer register and approval gate. For UK transfers, select UK adequacy, UK IDTA, UK Addendum, BCRs or a valid exception as applicable and complete the required UK assessment; for EU transfers, use EU adequacy, SCCs, BCRs or another valid Chapter V tool and assess supplementary measures. **PRIORITY:** P0.

### Finding TRANS-2 — Remote access must be analyzed as access, not hidden by hosting location

**FINDING:** A UK/EU document can leave the legal region even if the database remains in the UK/EEA. **EVIDENCE:** Architecture gives Processing Entities document/work-item access; the UI says Babui Limited in Bangladesh may process data; V3 entity RLS exposes assigned work. **LEGAL/REGULATORY BASIS:** EDPB transfer guidance uses a functional analysis: an exporter subject to GDPR makes personal data available to an importer in a third country; separate-organisation remote access generally requires Chapter V analysis. Whether access by CarbonTally’s own employee differs from access by a separate company must be confirmed on facts. **CARBONTALLY IMPACT:** “Data stays in Supabase UK/EU” would be incomplete if Bangladesh workers can view or download it. **CURRENT STATE:** Entity scope exists, but worker device, download, screenshot, printing, local cache and support controls are not evidenced. **GAP:** No documented remote-access model or technical enforcement. **RECOMMENDATION:** Record every third-country access path; use browser-isolated workspaces, no local download/print, watermarking, DLP, device/identity controls, session logging, least privilege, short-lived access and verified deletion; include the path in customer disclosures and transfer assessments. **PRIORITY:** P0.

## 7. UK Data Residency

### Finding RES-UK-1 — UK-only residency is not a general UK legal requirement

**FINDING:** The statement “UK law requires all data to remain in the UK” would be incorrect without a specific contract or rule. **EVIDENCE:** ICO guidance provides lawful routes for restricted transfers rather than a universal UK-localisation rule. **LEGAL/REGULATORY BASIS:** UK GDPR international-transfer regime: adequacy regulations, appropriate safeguards and exceptions. **CARBONTALLY IMPACT:** CarbonTally may choose UK-only as a product tier, but must not present it as a universal statutory requirement. **CURRENT STATE:** No verified live region/backup evidence; project documents discuss possible UK-London or EU-West placement. **GAP:** No region-specific deployment and backup attestation. **RECOMMENDATION:** Maintain a verified UK residency profile with region, database, Storage, logs, backups, support, subprocessors and failover locations; separately label it as law, contract, procurement, customer option or best practice. **PRIORITY:** P1 for a UK-residency product; P0 before claiming it.

### Finding RES-UK-2 — UK customer acceptance must be conditional on actual service configuration

**FINDING:** The code baseline contains location-neutral deployment files and no CarbonTally-owned evidence of provider-region selection. **EVIDENCE:** `vercel.json`, `frontend/vercel.json`, `backend/config.py`, Supabase configuration and provider environment names do not select or attest a production jurisdiction. **LEGAL/REGULATORY BASIS:** UK GDPR accountability and security; customer contract may impose stricter location or access conditions. **CARBONTALLY IMPACT:** Sales cannot promise UK data residency, UK-only support or UK-only backups from this repository. **CURRENT STATE:** Region is unknown. **GAP:** Location and failover facts are not tied to tenant configuration. **RECOMMENDATION:** Do not offer a “UK-only” tenant until verified; make region and transfer policy explicit in onboarding and enforce a deny-on-mismatch deployment check. **PRIORITY:** P0 before that claim; P1 otherwise.

## 8. EU/EEA Data Residency

### Finding RES-EU-1 — EEA-only is an optional architecture and procurement feature, not an automatic GDPR duty

**FINDING:** An EEA deployment can reduce transfer complexity but does not itself satisfy GDPR. **EVIDENCE:** Commission adequacy/SCC pages and DPC Chapter V guidance permit controlled third-country flows. **LEGAL/REGULATORY BASIS:** GDPR Articles 44–49. **CARBONTALLY IMPACT:** Irish/EU customers may still prohibit Bangladesh human access or non-EEA AI by contract even when primary storage is EEA. **CURRENT STATE:** No tenant-level region policy, subprocessor allowlist or destination deny control exists in evidence reviewed. **GAP:** Data residency cannot be selected or technically enforced per tenant. **RECOMMENDATION:** Build a region policy object spanning Storage, DB, queues, logs, AI, human processing and backup; fail closed when a workload’s destinations do not match. **PRIORITY:** P1; P0 for an EEA-only product promise.

## 9. AI Provider Risk

### Finding AI-1 — External AI is a configurable transfer and subprocessor surface

**FINDING:** The generic LLM engine can send document text to an arbitrary external endpoint, but no production provider governance is evidenced. **EVIDENCE:** `backend/infra/llm_client.py:44-174` accepts `base_url`, `api_key` and `model`, sends a bearer-authenticated `/chat/completions` request; `backend/engines/ai_extraction.py:133-138` places document text into the prompt. The repository has no production `LLMClient` composition or provider-specific policy found outside tests/docs. **LEGAL/REGULATORY BASIS:** UK/EU processor and international-transfer rules; controller transparency and security; EDPB controller/processor guidance. There is no blanket UK/EU prohibition on a US AI provider. **CARBONTALLY IMPACT:** Provider country, subprocessor role, retention, training, abuse monitoring, support access, legal requests and model endpoint determine whether the route is acceptable. **CURRENT STATE:** Technically possible; operationally ungoverned. **GAP:** No provider registry, allowlist, customer opt-in, DPA/SCC or UK Addendum, TRA/TIA, no-training commitment, deletion SLA, region pinning, prompt/content policy or audit record. **RECOMMENDATION:** Put AI behind a CarbonTally gateway with provider allowlist, tenant policy, region/destination check, redaction, minimised fields, encryption, no-training/no-retention contract where available, structured-output validation, prompt-injection handling, timeout/retry limits, per-document audit and provider deletion evidence. **PRIORITY:** P0 before external AI with customer documents.

### Finding AI-2 — Confidence is not validation or lawful automation governance

**FINDING:** AI output confidence and JSON validation do not establish accuracy, human oversight, or safe use. **EVIDENCE:** `AIExtractionEngine` accepts provider confidence in `0..1`, stores extracted fields and publishes an event; legacy PDF path routes low confidence to manual review. **LEGAL/REGULATORY BASIS:** UK/EU GDPR accuracy, fairness, security and accountability; any automated-decision rules depend on whether outputs produce legal or similarly significant effects. The EU AI Act may apply depending on CarbonTally’s role, use case and deployment, but emissions extraction is not automatically a high-risk use. **CARBONTALLY IMPACT:** A customer report can be materially wrong even when JSON is valid. **CURRENT STATE:** Human review is designed for low confidence, but thresholds, calibration, sampling, override, model/version and customer notice are not evidenced. **GAP:** No model-risk record or evidence that AI output cannot silently become an approved calculation. **RECOMMENDATION:** Require deterministic schema/range/source validation, model/provider/version lineage, independent QC sampling, customer-visible extraction method, human approval for exceptions and a documented AI Act/applicability assessment. **PRIORITY:** P1; P0 if AI is used for consequential customer decisions.

### Finding AI-3 — Provider terms control whether data is used for training

**FINDING:** The code cannot prove that an AI provider will not retain or train on customer documents. **EVIDENCE:** No provider contract, model card, regional endpoint declaration, retention setting or deletion response is in the baseline. **LEGAL/REGULATORY BASIS:** Transparency, purpose limitation, processor instructions, confidentiality and security duties under UK/EU GDPR. **CARBONTALLY IMPACT:** “API” does not mean “no training” or “no retention.” **CURRENT STATE:** Unknown. **GAP:** No customer disclosure or technical control. **RECOMMENDATION:** Make provider data-use terms a launch gate; prohibit consumer/free endpoints for customer data; document retention of prompts, outputs, abuse logs and human support copies; route only after DPA and transfer approval. **PRIORITY:** P0.

## 10. Bangladesh Human Processing

### Finding BD-1 — Bangladesh-based outsourced processing is ordinarily an international transfer

**FINDING:** UK/EU customer document → CarbonTally → Bangladesh-based separate processing company is ordinarily a restricted international transfer when CarbonTally makes personal data available to that company. **EVIDENCE:** `frontend/src/DataSecurity.jsx:292-316` expressly describes Babui Limited in Bangladesh and authorised personnel; migrations model Processing Entities and expose assigned work. **LEGAL/REGULATORY BASIS:** UK ICO international-transfer guidance and UK data protection test/TRA; GDPR Chapter V and EDPB transfer recommendations; DPC Chapter V guidance. Bangladesh is not evidenced as covered by a current UK or EU adequacy decision in the cited adequacy registers. **CARBONTALLY IMPACT:** A UK IDTA/Addendum or EU SCC arrangement, assessment, supplementary measures, subprocessor authorisation and worker controls are required unless counsel identifies a different factual/legal basis. ISO 27001, if genuine and in scope, is assurance evidence—not a transfer mechanism or substitute for a contract. **CURRENT STATE:** Product disclosure mentions a formal arrangement and ISO claim, but no certificate scope, contract, assessment or technical evidence was provided. **GAP:** No approved Bangladesh transfer pack. **RECOMMENDATION:** Before use, verify legal entity and certificate scope; execute CarbonTally–provider DPA and flow-down customer terms; obtain UK/EU authorisation; complete UK data protection test and EU TIA; apply minimisation, pseudonymisation, isolated workspace, no-download/DLP, access expiry, training/confidentiality, background checks where lawful, incident notice, audit, deletion and exit controls. **PRIORITY:** P0 before Bangladesh access.

### Finding BD-2 — “Human review” is not a legal exemption

**FINDING:** Routing work to a person instead of an AI provider does not remove privacy, security or transfer obligations. **EVIDENCE:** `manual_extraction_items`, `manual_review_queue`, entity staff and reviewer/QC records carry source files and extracted data. **LEGAL/REGULATORY BASIS:** UK/EU GDPR regulates processing regardless of whether it is automated; remote access and a separate organisation are relevant Chapter V facts. **CARBONTALLY IMPACT:** Human workers can copy, photograph, download or disclose documents unless the workspace and contract prevent it. **CURRENT STATE:** Entity scoping and mediated customer communication are architectural intentions; device and physical-environment controls are absent from code evidence. **GAP:** No worker assurance pack or measurable control evidence. **RECOMMENDATION:** Issue no human-processing access token without tenant/region eligibility, least privilege, session recording metadata, data-loss controls, watermarking, no local storage, approved devices/network, confidentiality/training and revocation/deletion checks. **PRIORITY:** P0.

## 11. Cloud/Subprocessor Risk

### Finding CLOUD-1 — Cloud provider chain is not mapped or customer-disclosed

**FINDING:** Supabase/PostgreSQL/Storage, deployment providers, email and any AI/human provider form a subprocessor chain that is not fully evidenced. **EVIDENCE:** Supabase client and Storage code, Vercel config, Render URLs/config references, Resend dependency, and external LLM client are present; no current vendor register, DPAs, locations, subprocessors, security reports or customer notification process was found. **LEGAL/REGULATORY BASIS:** UK GDPR Article 28 and GDPR Article 28 require processor contract controls and processor/subprocessor authorisation; security duties require appropriate measures. **CARBONTALLY IMPACT:** A change in cloud support region or subprocessor can change transfer and customer-contract risk without a code change. **CURRENT STATE:** Provider names are partly inferable but production tenant and subprocessor facts are unknown. **GAP:** No versioned subprocessor inventory with notice/objection, region, purpose, retention, certifications and exit plan. **RECOMMENDATION:** Maintain a vendor register and public/customer subprocessor list; require approval workflow, change notice, contractual audit/assistance/deletion/return clauses, region/failover record and annual reassessment. **PRIORITY:** P0.

### Finding CLOUD-2 — Backups and support access can defeat residency claims

**FINDING:** Database/Storage backups, logs, snapshots, support tickets and provider operations are not represented in the region policy. **EVIDENCE:** Schema has backup-frequency/retention/location fields, but no executable CarbonTally backup job or restore test was found; architecture explicitly includes backups/support. **LEGAL/REGULATORY BASIS:** UK/EU security, accountability, processor and Chapter V rules apply to copies and access, not only primary tables. **CARBONTALLY IMPACT:** A “UK-only” or “EEA-only” claim could be false through backups or provider support. **CURRENT STATE:** Unknown. **GAP:** No backup inventory, encryption/key ownership, immutable retention, regional failover, restore evidence or deletion propagation. **RECOMMENDATION:** Add backup/restore evidence to each region profile; document PITR and Storage backup locations, key management, support-access approval, restore isolation, retention and erasure limitations; contractually restrict support and cross-region failover. **PRIORITY:** P0 for residency claims; P1 otherwise.

## 12. Ireland/HSE

### Finding IE-1 — HSE is a customer/procurement profile, not a blanket residency rule

**FINDING:** No authoritative evidence establishes that HSE requires every supplier’s data to remain in Ireland. **EVIDENCE:** Repository contains Ireland/SEAI factor support and HSE references in project planning, but no HSE contract, tender, security schedule or current HSE supplier rule was supplied; HSE public data-protection pages were not retrievable in this environment. **LEGAL/REGULATORY BASIS:** GDPR/Irish Data Protection Act and DPC Chapter V apply as law; HSE procurement/security requirements would be contract or procurement requirements and must be read from the applicable tender/contract. **CARBONTALLY IMPACT:** CarbonTally must not claim “HSE-compliant,” “Ireland-only,” or “HSE-approved” based on the repository. **CURRENT STATE:** IE factor localisation is not proof of HSE readiness. **GAP:** No HSE-specific due diligence, DPIA input, security schedule, data-location clause, incident SLA, audit/exit or subprocessor approval. **RECOMMENDATION:** Ask HSE/customer counsel for the applicable contract and security requirements; map them separately from GDPR; provide a vendor, architecture, incident, resilience and transfer pack. **PRIORITY:** P1 for HSE sales; P0 for a contractual HSE deployment.

### Finding IE-2 — SEAI/Irish factor correctness is separate from personal-data compliance

**FINDING:** Irish factor support helps reporting correctness but does not prove data protection compliance. **EVIDENCE:** Provider architecture and `IE`/SEAI factor code exist; no legal control is coupled to factor selection. **LEGAL/REGULATORY BASIS:** GDPR duties attach to personal data processing, while factor provenance is a product/data-quality issue. **CARBONTALLY IMPACT:** A correct SEAI factor can still be processed by an unlawful subprocessor, and a compliant transfer can still produce a wrong report. **CURRENT STATE:** Separate concerns are appropriately modelled. **GAP:** Customer assurance materials may conflate them. **RECOMMENDATION:** Keep a separate factor-methodology assurance pack and privacy/security assurance pack. **PRIORITY:** P2.

## 13. UK NHS

### Finding NHS-1 — NHS England requirements are contractual/procurement and security requirements, not a blanket UK-localisation rule

**FINDING:** NHS customers will likely require evidence beyond ordinary commercial GDPR compliance, but no source reviewed establishes that all NHS supplier data must stay in the UK. **EVIDENCE:** The official NHS Data Security and Protection Toolkit portal exists; the repository contains no completed DSP Toolkit submission, NHS contract, DTAC assessment, DSPT evidence or NHS-specific clinical/safety determination. **LEGAL/REGULATORY BASIS:** NHS customer requirements arise from the applicable NHS England procurement, DSPT/DTAC and contract framework, alongside UK GDPR and the common-law duty of confidentiality where applicable. The exact customer category and data determine the requirement. **CARBONTALLY IMPACT:** CarbonTally should expect a detailed assurance questionnaire and possible flow-down terms. **CURRENT STATE:** No NHS readiness evidence. **GAP:** No DSPT/DTAC mapping, NHS subprocessor approval, clinical-risk boundary, support model or UK hosting evidence. **RECOMMENDATION:** Treat DSPT, DTAC, Cyber Essentials Plus/ISO 27001, penetration-test evidence, incident SLAs, business continuity, privileged-access logs, subprocessor controls and data-location answers as customer-gated deliverables; verify the exact tender. **PRIORITY:** P1 for NHS pursuit; P0 before NHS data processing under contract.

### Finding NHS-2 — CarbonTally must avoid implying clinical status

**FINDING:** CarbonTally’s emissions calculations and document review are not shown to be a clinical service. **EVIDENCE:** Repository functionality concerns emissions, reports, OCR, AI extraction and human validation; no clinical data model or clinical safety case was found. **LEGAL/REGULATORY BASIS:** NHS procurement and applicable product classification depend on intended use; this is not determined solely by an NHS customer. **CARBONTALLY IMPACT:** Marketing must not claim NHS approval, NHS certification or clinical assurance without the relevant assessment. **CURRENT STATE:** Unknown customer use cases. **GAP:** No intended-use and data-classification statement. **RECOMMENDATION:** Define non-clinical scope and prohibit clinical reliance unless a separate regulatory assessment is completed. **PRIORITY:** P1.

## 14. Financial Services

### Finding FIN-1 — FCA/PRA outsourcing expectations can flow through the customer contract

**FINDING:** FCA/PRA outsourcing and operational-resilience requirements do not automatically regulate CarbonTally merely because a bank or regulated firm is a customer, but the customer may flow them down. **EVIDENCE:** CarbonTally has billing, audit, reporting, provider and export surfaces; no FCA/PRA customer contract or regulated-service classification was supplied. **LEGAL/REGULATORY BASIS:** FCA FG16/5 and PRA SS1/21 address regulated firms’ outsourcing/third-party risk; applicability is customer- and service-specific. UK GDPR remains applicable to personal data. **CARBONTALLY IMPACT:** A financial customer may demand audit rights, material-outsourcing approval, subprocessor notice, location/access disclosure, resilience, exit/portability, incident cooperation, records and concentration-risk information. **CURRENT STATE:** Evidence/audit concepts exist, but assurance artefacts and tested RTO/RPO are not evidenced. **GAP:** No enterprise outsourcing pack. **RECOMMENDATION:** Build a supplier assurance pack with service description, data map, controls, SOC/ISO evidence where real, pen-test summary, RTO/RPO, BCP/DR tests, access review, subprocessor register, exit plan and incident obligations. **PRIORITY:** P1 for regulated financial customers; P2 otherwise.

## 15. DPIA

### Finding DPIA-1 — A DPIA is likely and should precede launch of the combined processing model

**FINDING:** The combination of document ingestion, OCR/AI extraction, human review, profiling of worker performance, third-country access and potentially large-scale customer processing is likely to merit a DPIA; the mandatory threshold must be confirmed against actual scale and data. **EVIDENCE:** AI engine, OCR, human/entity workflow, staff performance tables, audit logs, confidence scoring and international processing are in the baseline. **LEGAL/REGULATORY BASIS:** UK GDPR Article 35 and ICO DPIA guidance require a DPIA for processing likely to result in high risk; GDPR Article 35 and DPC guidance apply in Ireland/EU. A DPIA must assess necessity, proportionality, risks and measures, and be reviewed as processing changes. **CARBONTALLY IMPACT:** A DPIA can expose unacceptable Bangladesh/AI routes before customers do. **CURRENT STATE:** No completed DPIA or residual-risk acceptance found. **GAP:** No system boundary, data inventory, threat model, consultation, residual risk, transfer linkage or review trigger. **RECOMMENDATION:** Complete a DPIA covering customer documents, workers, AI/OCR, provider chain, rights, wrong-report risk, confidentiality and transfers; link it to the RoPA, TRA/TIA, contracts and release gates; consult the supervisory authority if high residual risk cannot be mitigated. **PRIORITY:** P0.

## 16. Security

### Finding SEC-1 — V3 controls are promising but legacy duplication prevents a defensible security boundary

**FINDING:** The repository contains duplicated legacy and V3 implementations with inconsistent URL, upload, configuration and authorization behavior. **EVIDENCE:** `main.py` mounts legacy routers and the V3 router; legacy `routes/upload.py` has public URLs and an unauthenticated test upload, while V3 uses signed URLs; multiple document tables (`customer_documents`, `organization_files`, manual extraction records) coexist. **LEGAL/REGULATORY BASIS:** UK/EU GDPR Article 32 and ICO security guidance require measures appropriate to risk, including confidentiality, integrity, availability and restoration. **CARBONTALLY IMPACT:** Security review cannot establish which path is authoritative, and unreviewed legacy endpoints may process live data. **CURRENT STATE:** Tests cover substantial V3 behavior but are not a production control proof. **GAP:** No route inventory, disablement plan, API gateway policy, live RLS test or threat-model sign-off. **RECOMMENDATION:** Select one production composition root; remove or deny legacy document paths; maintain endpoint/data-class authorization matrix; use service-role only behind a narrow backend; add live tenant-isolation, Storage, export and privileged-operation tests. **PRIORITY:** P0.

### Finding SEC-2 — Error and debug logging can contain personal or operational data

**FINDING:** Several legacy paths print emails, IDs, exception strings, tracebacks and provider/storage errors. **EVIDENCE:** `backend/auth.py:152-187`, `backend/routes/upload.py:181-182` and `266-270`, and `backend/database.py` print authentication/configuration and exception details; the generic AI client includes provider response snippets in error details. **LEGAL/REGULATORY BASIS:** UK/EU security, data minimisation, confidentiality and breach-accountability duties. **CARBONTALLY IMPACT:** Logs may copy document/provider data into a less-controlled system and expose secrets or identifiers to operators. **CURRENT STATE:** Standard logging and audit abstractions exist, but redaction/retention/role access are not evidenced. **GAP:** No log classification, redaction, access policy, SIEM region or retention execution. **RECOMMENDATION:** Use structured redacted logs; never log token/email/document text/provider bodies; separate security audit from application diagnostics; restrict and encrypt logs; set tested retention/deletion and alerting. **PRIORITY:** P0.

### Finding SEC-3 — Service-role and public grants need live verification

**FINDING:** Migrations rely on service-role access and deny-by-default RLS, but the live database privilege/RLS state was not inspected. **EVIDENCE:** M8/V3 migrations grant service-role broad access and authenticated DML with policies; entity writes intentionally remain service-role/application controlled. **LEGAL/REGULATORY BASIS:** UK/EU GDPR security and accountability require effective, not merely declared, controls. **CARBONTALLY IMPACT:** A stale policy, grant, function security context or privileged API query can defeat tenant isolation. **CURRENT STATE:** Migration text and unit tests are evidence of intended state only. **GAP:** No production catalog snapshot, `pg_policies` review, role membership review, function `SECURITY DEFINER` review or RLS integration run. **RECOMMENDATION:** Before go-live, capture a redacted live control report: grants, policies, functions, Storage policies, service-role call sites, cross-tenant negative tests, backup access and admin access review. **PRIORITY:** P0.

## 17. Retention

### Finding RET-1 — Retention is configurable in schema but not an executed policy

**FINDING:** A default `data_retention_days` of 365 appears in upload settings, but no complete data-class retention schedule and automated deletion/archival execution was evidenced. **EVIDENCE:** `backend/routes/upload.py:55-75` defaults to 365; schema includes data/document/audit/backup retention fields; migrations show user anonymisation and soft lifecycle concepts but no complete Storage/object/log purge service. **LEGAL/REGULATORY BASIS:** UK/EU storage limitation requires no longer retention than necessary; retention may also be required by contract or sector rules, but GDPR does not supply one universal CarbonTally period. **CARBONTALLY IMPACT:** Indefinite documents, OCR output, AI prompts, exports, email logs and backups increase exposure and undermine DSAR/erasure. **CURRENT STATE:** Business/legal policy is explicitly unresolved in project material. **GAP:** No per-class basis, retention owner, legal hold, deletion proof, backup expiry or customer-configurable policy with minimum/maximum guardrails. **RECOMMENDATION:** Counsel-approved schedule for source files, derived data, reports, audit, security logs, email, support and backups; retention metadata per object; idempotent purge jobs; deletion propagation and restore/backup treatment; customer export-before-delete workflow. Do not invent statutory periods. **PRIORITY:** P0 for documented policy and rights handling; P1 for full automation where no data is yet live.

### Finding RET-2 — User anonymisation is not document erasure

**FINDING:** The `anonymise_user` function preserves a user UUID and scrubs identity, but this does not establish erasure of customer documents, Storage objects, worker copies, reports or provider data. **EVIDENCE:** RC2 function comments describe user anonymisation; document and Storage deletion paths are separate and mixed. **LEGAL/REGULATORY BASIS:** UK GDPR Article 17/GDPR Article 17 subject to exemptions and controller responsibilities. **CARBONTALLY IMPACT:** A DSAR/erasure response could be incomplete. **CURRENT STATE:** Partial identity procedure; end-to-end erasure not verified. **GAP:** No data-subject-to-object graph, exception/retention decision, customer-controller assistance runbook or completion evidence. **RECOMMENDATION:** Map identifiers to all copies and derived outputs; distinguish account deletion, customer-tenant deletion and data-subject erasure; make deletion job auditable and provider-aware. **PRIORITY:** P0.

## 18. Incident Response

### Finding IR-1 — Breach response and processor notification obligations are not evidenced

**FINDING:** No tested incident runbook was found covering detection, triage, customer notification, regulator notification, provider escalation, evidence preservation and cross-border impact. **EVIDENCE:** Audit and event infrastructure exists, but no operational breach playbook, contact rota, tabletop or notification template was found. **LEGAL/REGULATORY BASIS:** UK GDPR Article 33 requires controller notification to the ICO without undue delay and, where feasible, within 72 hours when the breach is likely to risk individuals; GDPR Article 33 has the corresponding EU rule. Processors notify controllers without undue delay under Article 33(2). **CARBONTALLY IMPACT:** Public URLs, wrong-tenant responses, worker copying, AI provider incidents and backup exposure require rapid classification. **CURRENT STATE:** Unknown. **GAP:** No severity taxonomy, clock, RACI, processor SLAs, evidence chain or customer communication path. **RECOMMENDATION:** Implement and rehearse a 24/7 incident process with a 72-hour decision clock, regulator/customer criteria, provider SLAs, transfer-specific escalation, immutable evidence, containment/revocation and post-incident DPIA/control updates. **PRIORITY:** P0.

## 19. Current Architecture Assessment

**Overall assessment: NOT READY for unrestricted UK/EU production processing.**

### Strengths evidenced

- V3 has explicit customer organisation and Processing Entity concepts rather than treating a processor as a customer.
- D32 private bucket and signed URL direction is materially better than public document URLs.
- D33 links source files, extraction items, calculation snapshots and emissions logs for provenance.
- Entity RLS uses active entity membership and restricts entity visibility to assigned entity surfaces.
- Customer-owned factors are separated from global factors and snapshots preserve factor identity.
- Repository tests cover many org/entity authorization and serialization scenarios.

### Blocking uncertainties/weaknesses

- Legacy and V3 paths coexist; the legacy surface includes public URL and unauthenticated test behavior.
- Production LLM wiring, provider identity, location and contractual terms are not evidenced.
- Bangladesh processing is disclosed as a possibility, but transfer and worker assurance controls are not evidenced.
- Region, failover, backup, support and subprocessor locations are unknown.
- Retention, DSAR/erasure, incident response and DPIA are not demonstrated end-to-end.
- Migration text and tests do not prove live database, Storage, provider or deployment state.
- Some tables hold document URLs/JSONB derived data in parallel, increasing deletion and authorization complexity.

## 20. Compliance Gap Matrix

| ID | Gap | Evidence status | Legal/expectation class | Priority | Exit evidence |
|---|---|---|---|---|---|
| G1 | Controller/processor, purpose and data-category register | Missing | Legal/accountability | P0 | Approved RoPA, role matrix, DPAs |
| G2 | UK/EU privacy notice and rights operations | Missing | Legal | P0 | Tested DSAR/erasure/rectification runbooks |
| G3 | Disable legacy public/unauthenticated document paths | Confirmed code gap | Legal/security | P0 | Route inventory, negative tests, live Storage test |
| G4 | Live tenant/RLS/service-role verification | Unverified | Legal/security | P0 | Redacted catalog and cross-tenant test report |
| G5 | Bangladesh transfer pack | Missing | Legal if used; contract | P0 before Bangladesh | IDTA/Addendum/SCC, assessment, safeguards, supplier evidence |
| G6 | External AI provider pack | Generic capability only | Legal if used; contract | P0 before AI | Provider allowlist, DPA, no-training/retention, region and assessment |
| G7 | Cloud/email/backup subprocessor register | Missing | Legal/contract | P0 | Current register, DPAs, locations, change process |
| G8 | DPIA for combined model | Missing | Legal if high-risk threshold met; strong governance | P0 | DPIA, residual-risk approval, consultation decision |
| G9 | Retention/deletion/backup lifecycle | Partial settings only | Legal/accountability | P0/P1 | Counsel-approved schedule and tested jobs |
| G10 | Breach/incident process | Missing | Legal | P0 | Tabletop, 72-hour clock, SLAs and contact rota |
| G11 | UK residency option | No region evidence | Contract/customer expectation | P1 | Region/backup/support attestation and enforcement |
| G12 | EEA residency option | No region evidence | Contract/customer expectation | P1 | Tenant region policy and destination deny controls |
| G13 | NHS DSPT/DTAC/procurement pack | Missing | Contract/procurement | P1 for NHS | Applicable tender mapping and evidence pack |
| G14 | FCA/PRA outsourcing pack | Missing | Customer regulatory flow-down | P1 for regulated finance | RTO/RPO, exit, audit, subprocessor and resilience pack |
| G15 | External independent assurance | Not assessed | Enterprise expectation | P2 | ISO/SOC/pen-test evidence where actually held |
| G16 | Cryptographic external evidence ledger/archival | Not present | Best practice/enterprise | P3 | Independent archive/anchoring design if required |

## 21. Target Architecture

1. **Policy control plane:** Tenant profile contains data region, permitted destinations, human-processing eligibility, AI eligibility, retention class, legal hold and approved subprocessors. Every job evaluates the policy and fails closed.
2. **One document gateway:** Upload, view, repair, extraction, review and export all use one authorization service. Store canonical object paths, never public URLs; issue short-lived signed URLs only after tenant/entity authorization. Generated copies inherit the source tenant path and policy.
3. **Regional data plane:** Separate UK and EEA deployment profiles for database, Storage, queues, logs, backups and failover. Keep a destination ledger for support and subprocessors. Do not call a deployment “UK-only” or “EEA-only” unless every copy and access path is included.
4. **Provider gateway:** AI/OCR/email adapters are registered vendors with country, transfer tool, retention, training, subprocessor, region and deletion metadata. The gateway strips unnecessary fields, tags tenant/model/version, blocks unapproved destinations and writes a minimal audit record.
5. **Human-processing workspace:** Assign atomic work items, expose only necessary source data, use isolated browser sessions, no download/print, watermarking, DLP, device/identity assurance, access expiry and revocation. Keep customer, CarbonTally staff and Processing Entity roles separate.
6. **Evidence and lineage plane:** Link source object → extraction item → human/AI method → mapping/factor → calculation snapshot → validation/QC → approval → report/export. Preserve algorithm/provider/model/version and source page/hash without copying source text into logs.
7. **Privacy operations plane:** RoPA, DPIA, transfer register, vendor register, rights request workflow, retention ledger, legal holds, deletion propagation and regulator/customer incident workflow.
8. **Assurance plane:** Live RLS/Storage negative tests, privileged-query review, quarterly access review, restore rehearsal, subprocessor review, AI evaluation, worker QC sampling and regional failover evidence.

## 22. Product Opportunities

- “UK region” and “EEA region” product profiles with independently verified scope.
- Customer-controlled “no external AI” and “no non-UK/non-EEA human processing” switches.
- Managed-processing supplier transparency page with approved entities and service countries.
- AI-free deterministic/OCR tier for sensitive documents.
- Evidence bundle export: source lineage, factor version, reviewer/QC history, approval and report hash.
- Customer retention and legal-hold controls with clear non-negotiable minimums.
- Enterprise trust centre containing DPAs, subprocessor list, security summary, incident process, RTO/RPO and residency definitions.
- Regional routing and destination policy as a billable enterprise capability, only after it is technically enforced.

## 23. Priority Roadmap

### P0 — before relevant customer data

1. Freeze a single production API/document path; disable legacy public URLs and `/api/test-upload`; run live cross-tenant and Storage tests.
2. Complete controller/processor, RoPA, privacy notice, lawful-basis, data-category and rights/erasure pack.
3. Complete DPIA and UK/EU transfer register; no Bangladesh or external AI route until approved.
4. Establish provider/subprocessor register and signed DPAs, including hosting, Storage, email, AI and human processors.
5. Implement retention classes, deletion propagation, backup treatment and incident response with 72-hour decision clock.
6. Remove sensitive debug/error content from logs; define log region, retention and access.

### P1 — before commercial UK/EU/NHS/finance launch

1. Verify and document actual regions, failover, backups and support access.
2. Ship tenant destination policies and UK/EEA profiles where sold.
3. Deliver AI gateway, provider allowlist, no-training/retention controls and human-review safeguards.
4. Produce NHS-specific or finance-specific customer evidence only against the applicable contract/tender.
5. Rehearse DSAR, erasure, incident, restore and subprocessor replacement.

### P2 — enterprise/regulatory readiness

1. Independent penetration test and assurance report; ISO/SOC certification only if genuinely held and scoped.
2. Formal supplier audits, quarterly privileged access reviews, RTO/RPO tests and customer-facing trust centre.
3. Regional failover and exit portability with provider replacement drills.
4. Formal model-risk and AI evaluation programme.

### P3 — future enhancement

1. External cryptographic anchoring of evidence if customers require independent tamper evidence.
2. Multi-region active/active processing and confidential-computing options.
3. Advanced privacy-preserving extraction and customer-managed keys where economically justified.

## 24. Questions for Privacy Counsel

1. For each service purpose, is CarbonTally processor, controller, or joint controller, and what are the customer instructions and independent purposes?
2. Are source invoices likely to contain special-category, employee, financial, location, or other sensitive personal data in the intended markets?
3. Does the Bangladesh arrangement meet the factual definition of a separate processor/subprocessor, and which UK IDTA/Addendum and EU SCC modules apply?
4. What UK data protection test/TRA and EU TIA methodology, supplementary measures and review frequency are required for Bangladesh, US AI, email, hosting and support?
5. Is any current or planned US AI provider covered by the relevant EU-US Data Privacy Framework scope and UK Extension, and is reliance appropriate for this data?
6. Are AI extraction outputs or worker-performance metrics subject to automated-decision, profiling, employment, or sector rules in any customer use case?
7. Is a DPIA mandatory at planned scale, and should the ICO/DPC or customer DPO be consulted?
8. What data retention periods are justified by purpose, customer contract, accounting, legal claims, audit and sector rules? Which data must be deleted versus preserved under legal hold?
9. What exact HSE/NHS/financial-customer contract and procurement requirements apply, and which are contractual rather than law?
10. Can CarbonTally use a single UK or EEA region with foreign support, backups or human access, or must specific customers receive a destination-deny profile?
11. What privacy notice, cookie/analytics, subprocessor notice and customer authorisation wording is required?
12. Is CarbonTally required to appoint a DPO, UK/EU representative, or named security/privacy contact for the intended operations?

## 25. Source Register

All web sources below were consulted or attempted on 24 August 2026. Project files are evidence of implementation intent, not authoritative legal sources.

### Primary legal and regulatory sources

1. **ICO — International transfers hub**, including current links to adequacy regulations, appropriate safeguards and transfer risk assessment/data protection test:  
   <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/>
2. **ICO — Adequacy regulations**, current UK adequacy guidance and UK Extension distinction:  
   <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/adequacy-regulations/>
3. **ICO — Appropriate safeguards**, including UK IDTA and Addendum:  
   <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/appropriate-safeguards/>
4. **ICO — Completing a transfer risk assessment**, now referring to the UK legislative “data protection test”:  
   <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/completing-a-transfer-risk-assessment/>
5. **ICO — Data Protection Impact Assessments:**  
   <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/>
6. **ICO — A guide to data security:**  
   <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/security/a-guide-to-data-security/>
7. **EDPB — Guidelines 07/2020 on controller and processor concepts:**  
   <https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-072020-concepts-controller-and-processor-gdpr_en>
8. **European Commission — Standard Contractual Clauses:**  
   <https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en>
9. **European Commission — Adequacy decisions:**  
   <https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en>
10. **Irish Data Protection Commission — Transfers to third countries/international organisations:**  
    <https://www.dataprotection.ie/en/organisations/international-transfers/transfers-personal-data-third-countries-or-international-organisations>
11. **UK legislation — Data Protection Act 2018:**  
    <https://www.legislation.gov.uk/ukpga/2018/12/contents>
12. **EUR-Lex / GDPR consolidated text**, Articles 28, 32, 35 and Chapter V should be checked against the current official consolidated text for legal drafting:  
    <https://eur-lex.europa.eu/eli/reg/2016/679/oj>

### Sector and security sources

13. **NHS Data Security and Protection Toolkit official portal:**  
    <https://www.dsptoolkit.nhs.uk/>
14. **NHS England information governance/security material:** use the current NHS England procurement and DSPT/DTAC materials applicable to the customer and tender; no blanket NHS-only location conclusion was drawn from the portal.
15. **HSE data-protection landing pages:**  
    <https://www.hse.ie/eng/gdpr/> and <https://www.hse.ie/eng/about/who/data-protection/>  
    These pages were not retrievable during this audit; HSE-specific conclusions are therefore framed as questions/contract requirements, not asserted legal facts.
16. **UK National Cyber Security Centre — Cloud security guidance:**  
    <https://www.ncsc.gov.uk/collection/cloud>
17. **FCA FG16/5 — Guidance for firms outsourcing to the cloud and other third-party services:** verify the current FCA publication and applicability for the customer’s regulated service.
18. **PRA SS1/21 — Outsourcing and third-party risk management:** verify the current Bank of England/PRA publication and applicability for the customer.

### CarbonTally repository evidence inspected

- `backend/main.py`, `backend/auth.py`, `backend/config.py`, `backend/database.py`
- `backend/routes/upload.py`, `backend/api/v3_documents.py`, `backend/api/v3_exports.py`
- `backend/services/storage.py`, `backend/infra/llm_client.py`, `backend/engines/ai_extraction.py`
- `supabase/migrations/20260803000000_rc2_rls.sql`
- `supabase/migrations/20260807070000_add_new_table_rls.sql`
- `supabase/migrations/20260810000000_v3m1_processing_entities.sql`
- `supabase/migrations/20260810010000_v3m2_entity_relationships.sql`
- `supabase/migrations/20260810020000_v3m3_customer_factors.sql`
- `supabase/migrations/20260810040000_v3m5_issues.sql`
- `supabase/migrations/20260810050000_v3m6_entity_rls.sql`
- `supabase/migrations/20260821020000_d22_processing_work_assignment.sql`
- `supabase/migrations/20260823000000_d32_private_documents_storage.sql`
- `supabase/migrations/20260823010000_d33_evidence_traceability.sql`
- `CarbonTally_DB_Schema_V3M2.sql`
- `frontend/src/DataSecurity.jsx`
- Architecture, audit, security, pricing and Ireland/SEAI project documents, treated as intended architecture only.

## Final Executive Questions — Explicit Answers

### 1. What must CarbonTally implement before accepting its first UK customer?

At minimum: choose and document the UK processing role; complete privacy notice/RoPA/lawful-basis and rights operations; sign the customer DPA; inventory and approve all subprocessors/transfers; complete a DPIA or documented threshold decision; disable legacy public/unauthenticated document paths; enforce private Storage and signed URLs end-to-end; verify live RLS and service-role isolation; implement retention/deletion, backup, logging and incident response; and verify actual region/support/backup facts. If any customer document will be accessed in Bangladesh or by an external AI provider, those routes need separate approval before use.

### 2. What must it implement before accepting its first Irish/EU customer?

All UK baseline controls plus EU GDPR/Irish DPC mapping, EU controller/processor terms, EU Chapter V transfer assessment and appropriate tool for every third-country flow, customer disclosure of the subprocessor chain, and an approved EU/EEA region profile if the contract requires it. It does **not** need all data to remain in Ireland/EEA as a general GDPR matter, but it must not imply that it does unless technically true.

### 3. What changes are necessary before using external AI providers?

Use an approved-provider gateway and allowlist; complete controller/processor and subprocessor terms; select and document UK/EU transfer mechanisms and assessment; confirm endpoint region, retention, training/no-training, abuse logs and support access; minimise/redact data; add tenant policy and destination blocking; validate output independently; preserve model/provider/version lineage; require human/QC controls; and disclose the provider. A US endpoint is not automatically forbidden, but provider and customer/sector terms may forbid it.

### 4. What changes are necessary before using Bangladesh-based processing teams?

Treat a separate Bangladesh company as a likely subprocessor and international-transfer importer; complete the UK data protection test/TRA and EU TIA; execute the required UK IDTA/Addendum and/or EU SCC arrangement and customer authorisation; verify supplier and certificate scope; implement isolated browser workspace, no-download/DLP/watermarking, least privilege, worker confidentiality/training, device controls, access expiry, deletion and incident SLAs; and disclose the route. ISO 27001 alone is not enough.

### 5. What should CarbonTally build now to support future UK/EU data residency?

A tenant-level destination policy and region profile spanning primary DB/Storage, queues, logs, exports, backups, failover, support, AI, email and human processors; a provider gateway with destination deny controls; one document gateway; a transfer/subprocessor registry; and automated region-policy tests and evidence collection.

### 6. What should remain future architecture rather than immediate work?

Active/active multi-region, confidential computing, customer-managed keys, external cryptographic evidence anchoring, advanced privacy-preserving ML, and a full independent certification programme can remain P2/P3 unless a signed customer contract makes them prerequisites. Private Storage, route consolidation, legal/transfer controls, retention, incident response and live isolation cannot be deferred.

### 7. What would an enterprise/NHS/HSE customer likely ask CarbonTally to prove?

They will likely ask for the data map; controller/processor DPA; subprocessor list and change notice; UK/EU/third-country locations including backups/support; AI training/retention terms; access-control/RLS evidence; ISO/SOC/Cyber Essentials or equivalent evidence if held; penetration-test summary; DPIA/TRA/TIA; retention/erasure; incident contacts and notification SLAs; BCP/DR with RTO/RPO and restore tests; audit rights; exit/deletion/portability; staff vetting/training; and proof of the applicable DSPT/DTAC or financial-outsourcing requirements. These are often contractual/procurement expectations, not universal statutory location rules.

### 8. What should CarbonTally NOT claim publicly without legal confirmation?

Do not claim “all data stays in the UK,” “all data stays in Ireland/Europe,” “GDPR compliant,” “NHS compliant/approved,” “HSE compliant/approved,” “no international transfers,” “no AI training,” “ISO-certified” for CarbonTally based on a supplier certificate, “Bangladesh processing is legally cleared,” or “secure/private” while legacy public URL routes remain reachable. Also do not claim a US AI provider is prohibited by UK/EU law without a specific rule, contract or customer policy.

### 9. What are the five highest-priority architectural changes?

1. Consolidate to one authorization-enforced document gateway and eliminate public/unauthenticated legacy routes.
2. Add tenant destination/region policy across data, backups, support, AI, email and human processing.
3. Add a governed provider gateway for AI and all subprocessors, with transfer/retention/training controls.
4. Build the privacy-operations plane: RoPA, DPIA, transfer register, retention/deletion, rights and incident response.
5. Produce live assurance: RLS/Storage/service-role negative tests, privileged-access review, restore evidence and provider/worker audit evidence.

### 10. Which requirements are genuinely legal obligations versus merely enterprise expectations?

**Usually legal obligations, subject to facts:** UK/EU GDPR applicability, lawful/transparency/accountability, controller/processor contracts, security, storage limitation, data-subject rights, DPIA where high-risk criteria are met, Chapter V transfer mechanism/assessment, and breach notification/processor escalation.  
**Usually contract/procurement or sector requirements:** UK-only or EEA-only location, HSE/NHS DSPT/DTAC conditions, FCA/PRA outsourcing evidence flowed down by a regulated customer, specific RTO/RPO, named certifications, audit format, no-download worker controls, and customer-specific subprocessor approval.  
**Best practice/enterprise expectation unless contractually required:** regional tenant isolation, no-training AI, customer-managed keys, external evidence anchoring, independent certification, advanced DLP and active/active multi-region. Their status must be labelled per customer and contract; none should be presented as a universal UK/EU data-localisation law.

**HARD STOP — report complete.**