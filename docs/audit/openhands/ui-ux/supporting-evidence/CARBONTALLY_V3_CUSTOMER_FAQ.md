# CarbonTally V3 — Customer FAQ

This guide explains what CarbonTally does, how your data is processed, and
what you can expect from the service. It is written for business users, not
emissions engineers.

CarbonTally processes source documents into traceable, validated emissions
results. It is a data-processing and evidence platform, not just a calculator.

Every statement in this FAQ is based on the current CarbonTally V3 product and
its documented service model. Where something is planned but not yet
available, or where a detail still depends on a product decision, this guide
says so. Nothing here is a guarantee.

> **Note on the public website FAQ and Assistant.** The public website
> candidate (`website_candidate/frontend`) presents this content in two
> places: the `/faq` page and the public CarbonTally Assistant (a floating
> chatbot on every public page). Both use the same knowledge source
> (`src/public/faqData.js`), so they never diverge. The assistant answers from
> this FAQ with source attribution and answers "I don't have enough
> information" outside it; the architecture is documented in
> `CARBONTALLY_V3_AI_ASSISTANT_ARCHITECTURE.md`. The target-state wording
> intentionally does not expose internal implementation status. This document
> remains the canonical reference: it distinguishes what is available today,
> what is planned, and what is not offered, and every claim traces to the
> capability matrix.

---

## A. About CarbonTally

**What is CarbonTally?**

CarbonTally is a UK-based emissions data processing platform. You provide
source documents, such as utility bills, invoices or spreadsheets. CarbonTally
extracts the activity data, matches it to the right emission factor,
calculates the emissions, and gives you a traceable, validated result you can
review, approve and report on.

**What problem does CarbonTally solve?**

Turning messy, real-world documents into reliable emissions data takes a lot
of manual work. CarbonTally does that work for you: the data entry, the
mapping to the right activity, the factor matching, the calculation, and the
quality checks, all while keeping a record of where every number came from.

**Who is CarbonTally for?**

UK and EU businesses that need to understand their emissions. Typical users
are sustainability managers, finance and operations managers, procurement
managers, consultants, and SME owners.

**Is CarbonTally a calculator, a data-processing platform, a reporting
platform, or something else?**

It is a data-processing and evidence platform that includes calculation and
reporting. The calculation is part of a wider chain: source document,
extraction, mapping, factor selection, calculation, validation and review,
your approval, evidence, and report.

**What makes CarbonTally different?**

Two things stand out. First, traceability: every result can be traced back to
the source document, the extracted value, the factor used, and the checks it
passed. Second, human-assisted processing: trained CarbonTally staff and
approved processing partners handle the extraction and review work, and you
keep the final approval.

**Does CarbonTally process data for customers?**

Yes. CarbonTally offers human-assisted processing. Your documents are
processed by CarbonTally staff or approved processing partners through the
CarbonTally portal. This is the current service model.

**Can CarbonTally work with messy real-world source data?**

Yes, that is the point of the service. Documents that are inconsistent,
handwritten or poorly structured are read and entered by the processing team,
then mapped, validated and reviewed before you see the result.

---

## B. Documents and data input

**What documents can I upload?**

You can upload PDF files, images (JPG and PNG), and spreadsheets (CSV and
Excel). Upload them from the Documents area of your workspace.

**Can CarbonTally process scanned PDFs?**

You can upload scanned PDFs and they will be processed as part of the
human-assisted workflow. The processing team reads the document and enters
the data. Automatic character recognition of scans is planned but is not yet
part of the customer workflow.

**Can CarbonTally extract information from images?**

You can upload images such as JPG and PNG files and they will be processed in
the same human-assisted way. Automatic image reading is planned but is not
yet part of the customer workflow.

**Can CarbonTally process invoices?**

Yes. Invoices are a common document type. CarbonTally extracts the activity
data from them, such as quantities of fuel, electricity or goods, and maps it
to the right activity.

**Can CarbonTally process utility documents?**

Yes. Utility bills for electricity, gas, water and similar services are
typical source documents for the processing workflow.

**Can CarbonTally process spreadsheets?**

Yes. You can upload CSV and Excel files. CarbonTally can map the data in them
as part of processing. A self-service spreadsheet mapping experience is being
completed in the customer portal.

**What happens after I upload a document?**

Your document is stored securely, classified by type, and added to your
processing queue as an item awaiting processing.

**What happens if extraction fails?**

The item is flagged so you can see it needs attention. You can raise an issue
about it, and the processing team can ask you for a clearer copy.

**Can I correct extracted information?**

The extraction is done by the processing team. If you spot a problem, you can
raise an issue, and you can reject an item during customer review so it is
sent back for correction.

**Can CarbonTally process historical documents?**

You can upload past bills and invoices as source documents. Importing
historical data in bulk from another system is not currently offered.

---

## C. Extraction and OCR

**What is OCR?**

OCR (optical character recognition) means software reading the text out of a
scanned document or image automatically. CarbonTally's current processing is
human-assisted: trained staff read the document and enter the data. Automated
OCR is planned as part of recovering CarbonTally's full document-extraction
capability, but it is not yet in the customer workflow.

**Does CarbonTally use OCR for scanned documents?**

Not yet in the customer workflow. Scanned documents are handled by the
human-assisted processing team today.

**How does CarbonTally handle poor-quality documents?**

The processing team works from the document you provide. If something cannot
be read or is unclear, CarbonTally will ask for clarification or flag the item
so you can provide a better copy.

**Can extracted information be corrected?**

Yes, through the review and approval steps and through issues. Corrected items
are recalculated and recorded with their own evidence.

**How do I know where extracted information came from?**

Every result links back to its source document, including the page and line
where available. You can open the evidence record for any result to see this.

---

## D. Mapping

**What does "mapping" mean?**

Mapping means linking your data to the right activity. For example, "123 kWh
of electricity" is mapped to the electricity activity, in the right unit, for
your facility, before it is matched to an emission factor.

**Why does CarbonTally need mapping?**

Because raw data from documents does not say what it is. Mapping makes the
data structured and comparable, so the right factor can be applied and the
calculation is meaningful.

**Can I map my own data?**

Currently mapping is performed within CarbonTally's processing workflow by the
processing team. A self-service mapping screen is not yet part of the customer
portal.

**Can CarbonTally help map messy data?**

Yes. Handling messy or inconsistent data and mapping it to the right activity
is a core part of the service.

**What happens if CarbonTally cannot identify the correct activity?**

The item is flagged and a clarification is raised. CarbonTally will ask you
what the data is, or route the item back for correction.

**Can mappings be reviewed or corrected?**

Yes. Mapping is reviewed as part of validation and quality control, and can be
corrected before the result is final.

---

## E. Emission factors

**What is an emission factor?**

An emission factor is the number that converts a quantity of activity into
emissions. For example, it converts a quantity of electricity used into the
carbon emissions that quantity represents.

**Which emission factors does CarbonTally use?**

CarbonTally supports UK (DEFRA) factors, Irish (SEAI) factors, and your
organisation's own custom factors. Other countries' factor sets are not
currently supported.

**Does CarbonTally support UK DEFRA factors?**

Yes.

**Does CarbonTally support Irish and SEAI factors?**

Yes.

**Can customers use their own emission factors?**

Yes. Custom emission factors are an established CarbonTally capability. The
ability for customers to manage their own factors in the customer portal is
being completed; CarbonTally can add and use your approved factors as part of
your service.

**How are factors selected?**

CarbonTally matches your activity data to the appropriate factor, based on the
activity type, the unit, the country and the reporting year. Your
organisation's own approved custom factors take priority where they apply.

**Can I see which factor was used?**

Yes. Every result shows the factor used, and the evidence record lists it.

**Can I see the source and year of the factor?**

Yes. The factor source, set and reporting year are recorded with the
calculation.

**What happens if no factor is found?**

The item is flagged and CarbonTally will ask you what the activity is, or
discuss whether a custom factor is needed.

**Are factor changes traceable?**

Yes. The factor used for each calculation is recorded and kept with the
result's evidence.

---

## F. Calculations

**How does CarbonTally calculate emissions?**

CarbonTally multiplies your activity quantity by the relevant emission factor.
The calculation is done by CarbonTally's system, not by hand, and the result
is recorded automatically.

**Can customers change the calculated result?**

No. The result is produced by CarbonTally's calculation engine and recorded.
If the underlying data is wrong, the item is corrected and recalculated, and
the corrected result is recorded with its own evidence.

**Can I see how a result was calculated?**

Yes. The evidence record shows the quantity, the unit, the factor, the
calculation method and the result.

**Can I see which emission factor produced the result?**

Yes.

**Are calculations traceable?**

Yes. Each calculation links back to its source item and document, and forward
to its result and report.

**What happens when input data changes?**

The item is corrected and recalculated. The earlier result remains in your
history, and the new result is recorded with its own evidence, so the change
is traceable.

---

## G. Validation, review and quality control

**Does CarbonTally validate extracted data?**

Yes. Before a result is final, the item passes through validation, which
checks that the extracted and mapped data is complete and consistent.

**What is validation?**

Validation is a set of checks that the data makes sense: units are present,
quantities are usable, and the mapped activity and factor fit together. If a
check fails, the item is sent back for correction.

**What is review?**

Review is a person checking the item and its evidence before it moves on.
Reviewers confirm that the extraction, mapping and calculation look right.

**What is quality control (QC)?**

QC is an additional independent check with a quality score, notes and a
pass or fail decision. It happens after review.

**Who reviews processed data?**

CarbonTally staff review and QC items before results are submitted to you.
Where an approved processing partner did the work, the partner performs its
own review and QC first, and CarbonTally then performs a further review and
QC before the result reaches you.

**Can Processing Entities review their own work?**

Yes. Approved processing partners perform their own validation, review and QC
on the work assigned to them, through the CarbonTally portal.

**Does CarbonTally perform additional QC?**

Yes. CarbonTally performs its own validation, review and QC before results are
submitted to the customer.

**What happens when something fails QC?**

The item is sent back for correction, then validated, reviewed and checked
again.

**Can issues be sent back for correction?**

Yes. That is the normal path for items that fail validation or QC.

---

## H. Customer approval

**Does the customer review processed results?**

Yes. Customer review and final approval are part of the CarbonTally workflow.

**What does customer approval mean?**

It means your organisation confirms that the processed item and its result are
correct and can be treated as final. The result is recorded as approved.

**What can I see before approving?**

You can see the item, its source document, the extracted data, the mapping,
the factor used, the calculation and the evidence, so you can check before
you approve.

**Can I reject an item?**

Yes. You can reject an item and give a reason. The item is then sent back for
correction and will come back for your review again.

**What happens when I reject something?**

The item returns to the processing workflow with your reason, is corrected,
re-checked, and comes back to you for a fresh review.

**Does approval create an audit or evidence record?**

Yes. The approval, including who approved and when, is recorded with the
item's evidence.

**Who can approve?**

The rules for who can approve in your organisation are being confirmed. In
practice this is expected to be an owner or admin of your organisation, but
the final rule is still a product decision.

---

## I. Traceability and evidence

**Can I trace an emissions result back to its source document?**

Yes. Every result links back through its calculation, factor, mapping and
extracted value to the source document.

**What evidence is retained?**

The source document, the extracted data, the mapping, the factor used, the
calculation, the validation and QC checks, and the approval history are all
kept for each result.

**Can I see the source page or line item?**

Yes, where available. The evidence record shows the source file and the page,
and the extracted line item it came from.

**Can I see which emission factor was used?**

Yes.

**Can I see the calculation?**

Yes. The evidence record shows the inputs and the calculation used.

**Can I see review and QC history?**

Yes. Validation, review and QC stamps are part of the item's evidence.

**Are finalized evidence records immutable?**

Yes. Once a result is finalised, its evidence record is read-only. Corrections
create a new record rather than altering the old one.

---

## J. Reports and exports

**What reports can CarbonTally generate?**

CarbonTally generates an annual emissions report, a structured report of your
organisation's emissions for a reporting year. Report status is shown as
queued, generating, ready or failed.

**Can I export my data?**

Yes. You can export your emissions data and document data as CSV or JSON.

**Is PDF available?**

PDF report generation exists on the CarbonTally side. A PDF download button
in the customer portal is being added. Reports can currently be downloaded
from the portal as JSON.

**Is Excel available?**

You can upload Excel files as source documents. Export of results in Excel
format is not currently offered; CSV export is available.

**Is CSV available?**

Yes. Emissions and document data can be exported as CSV.

**What is included in reports?**

The annual report is a structured report covering your organisation's
emissions for the reporting year, built from your validated results.

**Can reports be regenerated?**

Yes. You can generate a report for a reporting year, and report versions are
tracked.

**Are report versions tracked?**

Yes. Report versions are kept so you can see which version is current.

---

## K. Consultants

**Can consultants manage multiple organisations?**

Yes. A consultant can work with more than one customer organisation, based on
an active relationship with each one.

**How does a consultant switch between clients?**

The consultant workspace has a client switcher. The screen always shows which
client the consultant is working on, so the active client is unmistakable.

**What can a consultant see?**

A consultant can see their clients' portfolio, processing status, reports,
issues and messages, and can message the client organisation. They can also
configure their firm's branding.

**Can consultants process data?**

Not currently. Consultants are advisory users who monitor and report. Whether
consultants get deeper processing access is a product decision that has not
been made.

**Can consultants view reports?**

Yes.

**Can consultants access evidence?**

Evidence is available through the reports they can view. Deeper direct access
to client evidence is a product decision that has not been made.

**Can consultants manage customer organisations?**

No. Consultants do not manage a customer organisation's settings or members.

**How is client separation maintained?**

Each client relationship is a separate, active grant. The consultant sees one
client at a time, and the system only shows data for the active client.

---

## L. Processing Entities

**What is a Processing Entity?**

A Processing Entity is an approved external team that performs human-assisted
processing work for CarbonTally, such as extraction and mapping.

**Why does CarbonTally use Processing Entities?**

To scale the human-assisted processing service while keeping all work inside
CarbonTally's controlled environment.

**What work can Processing Entity staff perform?**

They can perform extraction, mapping, validation, review and quality control
on the work assigned to them, through the CarbonTally portal.

**Can Processing Entities see customer documents?**

They can view the documents assigned to their work through the secure CarbonTally
portal, so they can extract the data. They see only what they are assigned.

**Can they download customer documents?**

No. Processing Entity staff work inside the CarbonTally portal and cannot
download customer source documents. This is enforced by the platform.

**How does CarbonTally control access?**

Access is controlled by assignment, by role, and by the portal's security
boundaries. Processing Entity staff only ever see work assigned to their
entity, and only through the portal.

**Can Processing Entities extract data?**

Yes, through the portal.

**Can they map data?**

Yes.

**Can they validate?**

Yes. Validation is part of the processing work they can perform.

**Can they review and do QC?**

Yes. Processing Entities perform their own review and QC on their work.
CarbonTally then performs a further review and QC before results reach you.

**How do they request clarification?**

Processing Entity staff can request clarification on an item. The request goes
to CarbonTally, which mediates the question, so the customer only ever
communicates with CarbonTally.

**Do Processing Entities communicate directly with customers?**

No. CarbonTally mediates all communication.

---

## M. Human-assisted processing

**Does CarbonTally offer document extraction services?**

Yes. Extraction of data from your documents is performed by CarbonTally staff
or approved processing partners as part of the service.

**Does CarbonTally offer data cleaning and mapping services?**

Yes. Cleaning and mapping your data to the right activities is part of the
processing service.

**Does CarbonTally offer review and QC?**

Yes. Review and quality control are built into the workflow, both by the
processing team and by CarbonTally before results are submitted to you.

**Does CarbonTally offer assisted or managed processing?**

Yes. The service model includes assisted and managed processing arrangements.
The practical details and terms depend on your plan, and should be confirmed
with CarbonTally.

**Is CarbonTally's processing automated or human-assisted?**

The current production workflow is human-assisted: people extract and review
your data through the portal, with automated calculation and validation
checks. Automated document reading is planned but is not yet part of the
customer workflow.

---

## N. Security and data handling

**Who can access my data?**

Your organisation's members (according to their roles), authorised CarbonTally
staff, approved processing partners (only the work assigned to them), and
consultants with an active relationship with your organisation.

**Are customer documents private?**

Yes. Documents are stored in CarbonTally's private storage and accessed
through controlled, time-limited links. They are not publicly accessible.

**Can Processing Entities download documents?**

No. They view assigned documents through the portal only.

**How is access controlled?**

Access is controlled by organisation boundaries, roles, and work assignment,
and enforced both in the platform and at the database level.

**Is data separated between organisations?**

Yes. Each organisation's data is isolated from every other organisation's
data, and the platform enforces this separation.

**How are documents accessed by processing staff?**

Processing staff open assigned work in the secure portal and view the
document there. They do not receive download links.

**Is access audited?**

Processing actions and evidence access are recorded, so there is a trace of
who did what.

**What happens to source documents?**

Source documents are stored securely as part of your evidence. Retention
periods are being finalised; if you need to know exactly how long documents
are kept, confirm this with CarbonTally.

**Does CarbonTally hold security certifications such as ISO 27001?**

CarbonTally does not currently publish certifications such as ISO 27001 or a
GDPR certification. If your organisation needs formal certifications or
specific commitments before sharing data, ask CarbonTally for the current
compliance position.

**What about data residency?**

CarbonTally's service is UK-first, with a gradual launch planned across the
EU and EEA. If you need a specific data-residency commitment, confirm it with
CarbonTally before sharing data. Legal and privacy statements for customers
are being finalised.

**Does CarbonTally guarantee compliance?**

No. CarbonTally does not guarantee that any particular legal or regulatory
outcome is achieved. Use the evidence CarbonTally provides with your own
advisers where compliance is required.

---

## O. Organisations and workspaces

**Can multiple people work in one organisation?**

Yes. Your organisation has a workspace with members. Members can be invited
and given a role.

**What are the Owner, Admin, Member and Viewer roles?**

Owner and Admin manage the organisation, such as members, facilities and
settings. Member can use the organisation's workspace. Viewer is intended as
a read-only role; the exact limits of the Viewer role are being confirmed and
may change.

**Can consultants work with multiple organisations?**

Yes, through separate active relationships.

**Can Processing Entities access multiple customers?**

They only access the specific work CarbonTally assigns to them, whatever
customer it belongs to. They cannot browse customer organisations.

**How is data separated?**

Organisation boundaries are enforced throughout the platform. You only see
your own organisation's data; consultants see one active client at a time;
processing partners see only assigned work.

---

## P. Billing and commercial

**How does CarbonTally charge for processing?**

CarbonTally works on a plan and credit model. Processing work and assisted or
managed processing requests are arranged through your account.

**What are credits?**

Credits are the unit used to account for processing work in your account. The
exact terms depend on your plan.

**What is assisted processing?**

Assisted processing is a processing request you place with CarbonTally, which
you review and approve before the chargeable work begins.

**What is managed processing?**

Managed processing is a processing arrangement you place with CarbonTally for
a defined piece of work. The practical terms depend on your plan.

**Can organisations see usage?**

Yes. Your billing area shows your plan, your credits and your orders.

**Can customers see orders?**

Yes. Orders show their status, and you approve assisted orders before work
begins.

**What is the price?**

Pricing and commercial terms depend on the applicable CarbonTally plan or
service and should be confirmed with CarbonTally.

---

## Q. What CarbonTally does not do

CarbonTally does not promise services it does not provide. In particular:

**CarbonTally is not an auditor, verifier or certification body.**

It does not provide independent emissions assurance, third-party audit, or
regulatory certification. It produces traceable results and evidence you can
use with your own advisers.

**CarbonTally does not guarantee compliance.**

It does not guarantee that any legal, regulatory or reporting requirement is
met. Where compliance is required, take CarbonTally's evidence to your
accountant, consultant, verifier or regulator.

**CarbonTally does not provide legal advice.**

**CarbonTally does not guarantee emission reductions.**

It measures and processes data; it does not set targets or guarantee outcomes.

**CarbonTally does not replace your accountant, consultant or verifier.**

**CarbonTally does not currently offer automated document reading.**

The production workflow is human-assisted. Automatic OCR and image extraction
are planned but not yet available to customers.

**CarbonTally does not currently support every country's emission factors.**

Supported factors are UK DEFRA, Irish SEAI and customer custom factors.

**CarbonTally does not currently offer public integrations.**

There are no established integrations with accounting, ERP or other systems.

**CarbonTally does not provide a general-purpose accounting or ERP system.**

It focuses on emissions data processing and evidence.

**CarbonTally does not publish security certifications or a verified data
residency guarantee today.**

Confirm the current compliance position with CarbonTally before relying on
either.

---

## R. Getting started

The journey has eight steps. Some are yours; some are CarbonTally's.

1. **Set up your organisation.** Your account is created and your organisation
   workspace is opened. You invite the people who will work in it.
2. **Upload or provide data.** You upload documents, such as PDFs, images or
   spreadsheets, in the Documents area. Your documents are stored securely.
3. **Extraction.** CarbonTally staff or an approved processing partner extract
   the activity data from your documents through the portal.
4. **Mapping.** The extracted data is mapped to the right activities, units
   and facilities.
5. **Processing and calculation.** The data is matched to emission factors and
   calculated by CarbonTally's system.
6. **Validation, review and QC.** The item passes validation, review and
   quality control, with corrections sent back when needed.
7. **Customer review and approval.** Your organisation reviews the item and
   approves or rejects it. Rejections are sent back with your reason.
8. **Results and reports.** Approved results become part of your evidence and
   are available in your reports and exports.

Steps 1, 2, 7 and 8 are customer actions. Steps 3, 4, 5 and 6 are CarbonTally
or processing partner actions, done through the portal.

---

## S. Troubleshooting and common questions

**My document failed to process — what should I do?**

Check its status in the Documents or Processing area. If it failed, you can
raise an issue, upload a clearer copy, or ask CarbonTally what went wrong.

**The extracted value is wrong — can it be corrected?**

Yes. Raise an issue, or reject the item during customer review with a reason.
It will be corrected, re-checked and returned to you.

**No emission factor was found — what happens?**

The item is flagged and CarbonTally asks what the activity is, or discusses
whether a custom factor is needed.

**I disagree with the mapping — what can I do?**

Raise an issue or reject the item at review with a reason. The mapping will
be corrected and re-checked.

**A processing item is waiting — why?**

Items wait when they are queued for the next stage, such as extraction,
review or QC. If an item has been waiting for a long time, raise an issue or
ask CarbonTally.

**Why is my item awaiting approval?**

Items move to your review when processing, validation and QC are complete.
Review it and approve or reject it.

**What happens if I reject an item?**

It goes back to the processing workflow with your reason, is corrected,
re-checked, and comes back to you.

**Can I upload another version of a document?**

Yes. You can upload a new version and raise an issue so the team knows to use
it.

**How do I trace a result back to its source?**

Open the result's evidence record. It shows the calculation, factor, mapping,
extracted value and source document, with the page where available.

---

## How to read this FAQ

Where an answer says something is planned or being completed, it is not
available to customers yet. Where an answer says a detail depends on your
plan or needs confirmation with CarbonTally, it is not a fixed promise.

If anything in this FAQ conflicts with your contract or an agreement with
CarbonTally, the contract or agreement is what counts. This FAQ does not
create guarantees.
