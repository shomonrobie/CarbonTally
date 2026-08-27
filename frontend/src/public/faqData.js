// Public website FAQ content.
// Target-state wording for the complete CarbonTally service, per the approved
// product/service model. Internal implementation status is intentionally not
// exposed here; the internal capability matrix is the source of truth for
// what is implemented today.
// Each item: id (URL slug), q, a, and optional related item ids.

export const FAQ_CATEGORIES = [
  {
    slug: 'getting-started',
    title: 'Getting started',
    intro: 'What CarbonTally is and how the service works.',
    items: [
      {
        id: 'what-is-carbontally',
        q: 'What is CarbonTally?',
        a: 'CarbonTally is a UK-first emissions data processing platform and service. You provide source data and CarbonTally turns it into structured, traceable, validated emissions results, with evidence and reporting. It is more than a calculator: software and human-assisted processing work together to get from messy source data to a defensible result.',
        related: ['how-the-service-works'],
      },
      {
        id: 'what-problem',
        q: 'What problem does CarbonTally solve?',
        a: 'Turning messy real-world source data into reliable emissions data normally means hours of manual work in spreadsheets. CarbonTally does that work in a controlled pipeline: documents and data are ingested, extracted, mapped to the right activities, matched to emission factors, calculated, validated, reviewed and evidenced, so the numbers can be traced and defended.',
        related: ['how-the-service-works'],
      },
      {
        id: 'who-for',
        q: 'Who is CarbonTally for?',
        a: 'UK and EU businesses that need to understand their emissions: sustainability, finance, operations and procurement teams, and SME owners. CarbonTally also serves carbon consultants and advisory firms working across multiple client organisations.',
        related: ['consultants-multiple-clients'],
      },
      {
        id: 'platform-or-service',
        q: 'Is CarbonTally a calculator, a platform, or a managed service?',
        a: 'It is both a platform and a service. The CarbonTally platform provides the processing pipeline, evidence and reporting. CarbonTally also offers human-assisted processing, where trained CarbonTally teams help with extraction, mapping, validation and review. You choose how much of the work CarbonTally does for you.',
        related: ['what-is-assisted-processing', 'how-the-service-works'],
      },
      {
        id: 'how-the-service-works',
        q: 'How does the CarbonTally service work?',
        a: 'The journey runs: source data, document and data ingestion, extraction, mapping, emission factor matching, calculation, validation, review and quality control, customer approval, evidence and traceability, and reporting. Each stage builds on the last, and every result carries its evidence with it.',
        related: ['what-happens-after-upload'],
      },
      {
        id: 'get-started',
        q: 'How do I get started?',
        a: 'CarbonTally is preparing for commercial launch. Contact CarbonTally for launch information. When your organisation is onboarded, you set up your workspace, invite the people who will work in it, and start providing source data.',
        related: ['what-is-carbontally'],
      },
    ],
  },
  {
    slug: 'documents-data',
    title: 'Documents and data',
    intro: 'The source data CarbonTally can work with.',
    items: [
      {
        id: 'what-documents',
        q: 'What documents can CarbonTally process?',
        a: 'CarbonTally processes the source documents and data behind your emissions: PDFs, scanned PDFs, images such as JPG and PNG, spreadsheets in CSV and Excel, invoices, utility bills and similar source records.',
        related: ['can-it-process-scanned'],
      },
      {
        id: 'can-it-process-scanned',
        q: 'Can CarbonTally process scanned documents?',
        a: 'Yes. Text is read from scanned documents and images as part of the document processing workflow, with human review where the source is difficult to read.',
        related: ['what-is-ocr', 'what-is-extraction'],
      },
      {
        id: 'can-it-process-spreadsheets',
        q: 'Can CarbonTally process spreadsheets?',
        a: 'Yes. CSV and Excel files can be provided as source data and mapped into the processing workflow alongside documents.',
        related: ['what-does-mapping-mean'],
      },
      {
        id: 'what-happens-after-upload',
        q: 'What happens after I provide my data?',
        a: 'Your data is stored securely, classified and brought into the processing workflow. You can see where each item is in the pipeline and what still needs attention.',
        related: ['how-the-service-works'],
      },
      {
        id: 'messy-historical-data',
        q: 'Can CarbonTally handle messy or historical data?',
        a: 'Yes. Handling inconsistent, handwritten or poorly structured source data is exactly what the service is for. Past bills and invoices can be provided as source documents for historical periods.',
        related: ['what-documents', 'what-problem'],
      },
    ],
  },
  {
    slug: 'extraction-ocr',
    title: 'Extraction and OCR',
    intro: 'How CarbonTally reads your source documents.',
    items: [
      {
        id: 'what-is-extraction',
        q: 'What is document extraction?',
        a: 'Extraction is the step where the activity data is pulled out of a source document, such as the quantities, units, dates and suppliers on an invoice or utility bill.',
        related: ['what-happens-after-upload'],
      },
      {
        id: 'what-is-ocr',
        q: 'What is OCR?',
        a: 'OCR, or optical character recognition, is the technology that reads text from scanned documents and images. CarbonTally supports document text extraction and OCR as part of its document processing workflow, with human review where required.',
        related: ['can-it-process-scanned'],
      },
      {
        id: 'how-scanned-processed',
        q: 'How does CarbonTally process scanned documents?',
        a: 'Scanned documents go through the same workflow as other source data. Text is read from the scan, and where the scan is unclear, the processing team reviews it by hand so the data is still captured accurately.',
        related: ['what-is-ocr', 'when-human-review'],
      },
      {
        id: 'difficult-documents',
        q: 'How does CarbonTally handle difficult documents?',
        a: 'Documents that are hard to read, incomplete or unusual are flagged for human review. If more information is needed, a clarification request is raised through the CarbonTally workflow and handled with you.',
        related: ['how-clarification-works'],
      },
      {
        id: 'when-human-review',
        q: 'When is human review involved?',
        a: 'Human review is part of the service wherever it adds quality: checking extracted data, resolving unclear source documents, confirming mappings and performing review and quality control before results reach you.',
        related: ['what-is-human-assisted-processing'],
      },
    ],
  },
  {
    slug: 'mapping-factors',
    title: 'Mapping and emission factors',
    intro: 'How activity data is organised and matched to emission factors.',
    items: [
      {
        id: 'what-does-mapping-mean',
        q: 'What does mapping mean?',
        a: 'Mapping links your data to the right activity. For example, a quantity of electricity on a utility bill is mapped to the electricity activity, in the right unit, for the right facility, so the correct emission factor can be applied.',
        related: ['how-factors-selected'],
      },
      {
        id: 'how-mapping-works',
        q: 'How does CarbonTally map activity data?',
        a: 'CarbonTally maps your data to standard activities with software assistance and human review. Messy data is cleaned and structured as part of the workflow, and uncertain mappings are checked before a result is produced.',
        related: ['messy-historical-data'],
      },
      {
        id: 'customer-mappings',
        q: 'Can customers provide their own mappings?',
        a: 'Yes. Where your organisation has its own way of describing activities, facilities or assets, that can be reflected in how your data is mapped, and mappings are reviewable.',
        related: ['how-mapping-works'],
      },
      {
        id: 'what-are-factors',
        q: 'What are emission factors?',
        a: 'An emission factor is the number that converts a quantity of activity into emissions, for example converting a quantity of electricity used into the carbon emissions that quantity represents.',
        related: ['how-factors-selected'],
      },
      {
        id: 'which-factor-sets',
        q: 'Which emission factor sets does CarbonTally support?',
        a: 'CarbonTally supports UK DEFRA factors, Irish SEAI factors, and organisation-specific custom emission factors. Factor details such as source, reporting year, country, unit and scope are recorded for every calculation.',
        related: ['custom-factors', 'factor-provenance'],
      },
      {
        id: 'custom-factors',
        q: 'Can customers use their own emission factors?',
        a: 'Yes. CarbonTally supports organisation-specific custom emission factors. Your approved factors are used in your calculations and take priority where they apply to your data.',
        related: ['which-factor-sets'],
      },
      {
        id: 'how-factors-selected',
        q: 'How does CarbonTally select the right factor?',
        a: 'CarbonTally matches your activity data to the appropriate factor based on the activity type, unit, country and reporting year, and records which factor was used for each calculation.',
        related: ['factor-provenance'],
      },
      {
        id: 'factor-provenance',
        q: 'Can I see which factor was used, and its source and year?',
        a: 'Yes. Every result shows the factor used, and its source, set and reporting year are recorded with the calculation so the basis of the number can be traced.',
        related: ['trace-result-to-source'],
      },
    ],
  },
  {
    slug: 'calculations-validation',
    title: 'Calculations and validation',
    intro: 'How results are calculated and checked.',
    items: [
      {
        id: 'how-calculated',
        q: 'How are emissions calculated?',
        a: 'Emissions are calculated by multiplying your activity quantity by the relevant emission factor. The calculation is performed by CarbonTally\u2019s system and recorded automatically, so results are consistent and traceable.',
        related: ['what-does-mapping-mean'],
      },
      {
        id: 'change-result',
        q: 'Can the result be changed?',
        a: 'The system produces the result. If the underlying data needs correcting, the item is corrected and recalculated, and the corrected result is recorded with its own evidence, so changes are always visible.',
        related: ['trace-result-to-source'],
      },
      {
        id: 'calculations-traceable',
        q: 'Are calculations traceable?',
        a: 'Yes. Every calculation links back to its source data and forward to its evidence, approval and report, so the chain behind any number can be followed.',
        related: ['trace-result-to-source'],
      },
      {
        id: 'what-is-validation',
        q: 'What is validation?',
        a: 'Validation is a set of automated checks that the data is complete, consistent and usable: units are present, quantities make sense, and the mapped activity and factor fit together. Items that fail are sent back for correction.',
        related: ['what-is-quality-control'],
      },
      {
        id: 'validation-fail',
        q: 'What happens if data fails validation?',
        a: 'The item is flagged and returned for correction, then validated again. You only see results that have passed the checks.',
        related: ['what-is-validation', 'approval-meaning'],
      },
    ],
  },
  {
    slug: 'review-qc-approval',
    title: 'Review, QC and approval',
    intro: 'Who checks the work, and your final say.',
    items: [
      {
        id: 'who-reviews',
        q: 'Who reviews processed data?',
        a: 'Processed data passes through review and quality control before it reaches you. Where an approved processing partner did the work, the partner performs its own review first, and CarbonTally then performs a further review and quality control before results are submitted.',
        related: ['what-is-quality-control'],
      },
      {
        id: 'what-is-quality-control',
        q: 'What is quality control?',
        a: 'Quality control is an independent check of the processed item against its source evidence, with findings and a pass or fail decision. It happens after review and before results are submitted to you.',
        related: ['who-reviews'],
      },
      {
        id: 'approval-meaning',
        q: 'What does customer approval mean?',
        a: 'Customer approval is your confirmation that a processed item and its result are correct and can be treated as final. You review the item, its source, the mapping, the factor and the calculation before you approve.',
        related: ['what-can-i-see-before-approval'],
      },
      {
        id: 'what-can-i-see-before-approval',
        q: 'What can I see before approving?',
        a: 'You can see the processed item with its source document, the extracted data, the mapping, the factor used and the calculation, so you can check the basis of the result before you approve.',
        related: ['approval-meaning', 'trace-result-to-source'],
      },
      {
        id: 'reject-item',
        q: 'Can I reject an item?',
        a: 'Yes. You can reject an item with a reason. It is sent back for correction, checked again, and returned to you for a fresh review.',
        related: ['approval-meaning'],
      },
      {
        id: 'approval-recorded',
        q: 'Is my approval recorded?',
        a: 'Yes. The approval, including who approved and when, is kept as part of the item\u2019s evidence, so the decision is traceable.',
        related: ['what-evidence-is-kept'],
      },
    ],
  },
  {
    slug: 'evidence-traceability',
    title: 'Evidence and traceability',
    intro: 'Where every number came from, and how to prove it.',
    items: [
      {
        id: 'trace-result-to-source',
        q: 'Can I trace a result back to its source?',
        a: 'Yes. Every result carries a full evidence chain: source, extraction, mapping, factor, calculation, validation and quality control, approval, and result. You can follow the chain in either direction to see how a number was produced.',
        related: ['what-evidence-is-kept'],
      },
      {
        id: 'what-evidence-is-kept',
        q: 'What evidence is kept?',
        a: 'For each result, CarbonTally keeps the source document, the extracted data, the mapping, the factor used, the calculation, the validation and quality control stamps, and the approval history.',
        related: ['trace-result-to-source', 'approval-recorded'],
      },
      {
        id: 'evidence-readonly',
        q: 'Are final evidence records read-only?',
        a: 'Yes. Once a result is finalised, its evidence record is read-only. Corrections create a new record rather than altering the old one, so the history stays intact.',
        related: ['change-result'],
      },
    ],
  },
  {
    slug: 'human-assisted',
    title: 'Human-assisted processing',
    intro: 'How CarbonTally combines software with people.',
    items: [
      {
        id: 'what-is-human-assisted-processing',
        q: 'What is human-assisted processing?',
        a: 'CarbonTally combines its software with trained teams who perform processing work through the CarbonTally platform: extraction, data cleaning, mapping, validation, review and quality control. You benefit from the automation and the judgement of people where it counts.',
        related: ['when-human-review'],
      },
      {
        id: 'what-teams-do',
        q: 'What work do CarbonTally\u2019s teams do?',
        a: 'The teams help with extraction, cleaning and mapping your source data, validating the results, reviewing and quality-checking the work, and resolving clarifications through the CarbonTally workflow.',
        related: ['what-is-human-assisted-processing'],
      },
      {
        id: 'how-clarification-works',
        q: 'How do processing teams ask questions about my data?',
        a: 'Clarification requests are raised through the CarbonTally workflow and handled by CarbonTally. You respond through CarbonTally, and the item continues through processing once the question is resolved.',
        related: ['difficult-documents'],
      },
      {
        id: 'what-are-processing-entities',
        q: 'What are Processing Entities?',
        a: 'Processing Entities are approved external teams CarbonTally works with to provide human-assisted processing capacity. They perform assigned work inside the CarbonTally platform, under CarbonTally\u2019s controls.',
        related: ['pe-download-documents', 'who-reviews'],
      },
      {
        id: 'pe-download-documents',
        q: 'Can Processing Entities download customer documents?',
        a: 'No. Processing teams work inside the CarbonTally platform on the work assigned to them. Customer documents remain protected and are never downloadable by processing partners.',
        related: ['what-are-processing-entities', 'documents-protected'],
      },
    ],
  },
  {
    slug: 'consultants',
    title: 'Consultants',
    intro: 'How consultants use CarbonTally with their clients.',
    items: [
      {
        id: 'consultants-multiple-clients',
        q: 'Can consultants work across multiple organisations?',
        a: 'Yes. A consultant can work with more than one client organisation, with each client relationship separately authorised.',
        related: ['client-separation'],
      },
      {
        id: 'consultant-client-switching',
        q: 'How does a consultant switch between clients?',
        a: 'The consultant workspace has a client switcher, and the screen always shows which client is active, so work is never applied to the wrong organisation.',
        related: ['client-separation'],
      },
      {
        id: 'what-consultants-see',
        q: 'What can a consultant see?',
        a: 'A consultant can see the active client\u2019s processing status, results, reports, issues and messages, and can message the client organisation.',
        related: ['consultants-multiple-clients'],
      },
      {
        id: 'client-separation',
        q: 'How is client separation maintained?',
        a: 'Each client relationship is separate, and the consultant works on one client at a time. Only the active client\u2019s data is shown, and access is controlled by each client\u2019s authorisation.',
        related: ['consultant-client-switching'],
      },
    ],
  },
  {
    slug: 'security-data',
    title: 'Security and data',
    intro: 'How CarbonTally protects your data.',
    items: [
      {
        id: 'who-can-access',
        q: 'Who can access my data?',
        a: 'Your organisation\u2019s members, authorised CarbonTally staff, approved processing partners working on assigned items, and consultants you have authorised. Access is controlled and scoped to what each person needs.',
        related: ['documents-protected'],
      },
      {
        id: 'documents-protected',
        q: 'How are my documents protected?',
        a: 'Documents are stored in CarbonTally\u2019s private storage and accessed through controlled links. They are not publicly exposed, and processing partners cannot download customer documents.',
        related: ['pe-download-documents'],
      },
      {
        id: 'data-separation',
        q: 'Is data separated between organisations?',
        a: 'Yes. Organisation boundaries are enforced across the platform, so each organisation only sees its own data.',
        related: ['who-can-access'],
      },
      {
        id: 'access-audited',
        q: 'Is access to my data audited?',
        a: 'Processing actions and evidence access are recorded, so there is a trace of who did what and when.',
        related: ['documents-protected'],
      },
      {
        id: 'security-certifications',
        q: 'What security certifications does CarbonTally hold?',
        a: 'CarbonTally is preparing for commercial launch. If your organisation needs formal certifications, or specific commitments about where and how data is handled, contact CarbonTally for the current compliance position before sharing data.',
        related: ['who-can-access'],
      },
    ],
  },
  {
    slug: 'reports-exports',
    title: 'Reports and exports',
    intro: 'What you get out of the platform.',
    items: [
      {
        id: 'what-reports',
        q: 'What reports does CarbonTally produce?',
        a: 'CarbonTally produces versioned structured reports built from your approved, evidenced results, so reporting comes from the verified data set rather than being re-keyed.',
        related: ['how-calculated'],
      },
      {
        id: 'report-formats',
        q: 'What formats are available?',
        a: 'CarbonTally provides structured reports and branded PDFs, plus CSV data exports of your emissions and document data, so you can take the data anywhere.',
        related: ['what-reports'],
      },
      {
        id: 'report-versions',
        q: 'Are report versions tracked?',
        a: 'Yes. Reports are versioned, so you can always see which version is current and how it was built.',
        related: ['what-reports'],
      },
    ],
  },
  {
    slug: 'billing-services',
    title: 'Billing and services',
    intro: 'How CarbonTally is offered commercially.',
    items: [
      {
        id: 'how-charged',
        q: 'How does CarbonTally charge for processing?',
        a: 'CarbonTally is offered on a plan with processing credits, together with assisted and managed processing services. The practical terms depend on your plan and service arrangement.',
        related: ['what-is-assisted-processing'],
      },
      {
        id: 'what-is-assisted-processing',
        q: 'What is assisted processing?',
        a: 'Assisted processing is where you request processing through CarbonTally and CarbonTally\u2019s teams perform the work for you, with your review and approval before chargeable work begins.',
        related: ['what-is-human-assisted-processing'],
      },
      {
        id: 'what-is-managed-processing',
        q: 'What is managed processing?',
        a: 'Managed processing is a defined processing arrangement delivered by CarbonTally for a specified piece of work, arranged through your account.',
        related: ['what-is-assisted-processing'],
      },
      {
        id: 'pricing',
        q: 'What does CarbonTally cost?',
        a: 'Pricing and commercial terms depend on the applicable CarbonTally plan or service and should be confirmed with CarbonTally.',
        related: ['how-charged'],
      },
    ],
  },
  {
    slug: 'boundaries',
    title: 'What CarbonTally does not do',
    intro: 'Clear boundaries so you know what to expect.',
    items: [
      {
        id: 'not-auditor',
        q: 'Is CarbonTally an auditor or verifier?',
        a: 'No. CarbonTally is not an independent auditor or verifier and does not provide regulatory certification. It produces traceable results and evidence you can use with your own advisers where assurance or certification is required.',
        related: ['trace-result-to-source'],
      },
      {
        id: 'not-compliance-guarantee',
        q: 'Does CarbonTally guarantee compliance?',
        a: 'No. CarbonTally does not guarantee that any legal or regulatory outcome is achieved. Where compliance is required, take CarbonTally\u2019s evidence to your accountant, consultant, verifier or regulator.',
        related: ['not-auditor'],
      },
      {
        id: 'not-legal-advice',
        q: 'Does CarbonTally provide legal advice?',
        a: 'No. CarbonTally does not provide legal advice.',
        related: ['not-compliance-guarantee'],
      },
      {
        id: 'not-reduction-guarantee',
        q: 'Does CarbonTally guarantee emission reductions?',
        a: 'No. CarbonTally measures and processes data; it does not set targets or guarantee outcomes.',
        related: ['what-problem'],
      },
    ],
  },
];
