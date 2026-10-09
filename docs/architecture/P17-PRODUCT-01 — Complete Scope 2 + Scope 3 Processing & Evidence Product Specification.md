P17-PRODUCT-01 — Complete Scope 2 + Scope 3 Processing & Evidence Product Specification
1. What the market tells us

The mature platforms are not simply "carbon calculators."

Watershed

Watershed currently advertises:

all 15 Scope 3 categories
automated PDF ingestion
APIs and integrations
AI data cleaning/standardisation
anomaly detection
500,000 built-in factors on its current site
calculation transparency and lineage
human review
supplier engagement
audit trails
reporting/disclosure
activity-based Scope 3
data-quality controls
scenario planning and reduction modelling.
Persefoni

Persefoni currently describes:

complete Scope 3 footprints from spend estimates through actuals
supplier engagement
calculation methods aligned with recognised accounting standards
an Integration Hub
Concur
Expensify
Navan
Google Sheets
utility integrations
automated business-travel ingestion.

Its Navan integration is particularly relevant to our discussion: it handles air, rail, taxi, rental car and hotel activity. Concur/Expensify similarly ingest commercial air, hotel and taxi activity.

That is almost exactly the business-trip scenario you described.

Normative

Normative emphasizes:

Scope 1/2/3 accounting
large factor libraries
automated matching
supplier/value-chain engagement
primary supplier data
secondary/spend-based data
supplier data requests
validation
supplier-specific emissions
progressive improvement from estimates to primary data.
Sweep

Sweep emphasizes:

collecting data from suppliers
mapping data across the value chain
collaboration with suppliers
tracking/approval/rejection/in-progress states
reporting
audit readiness
end-to-end Scope 3 and supplier engagement.
The important conclusion

The common architecture is:

DATA ACQUISITION
      ↓
DATA NORMALISATION
      ↓
CLASSIFICATION
      ↓
METHODOLOGY
      ↓
EMISSION FACTOR
      ↓
CALCULATION
      ↓
QUALITY / REVIEW
      ↓
SUPPLIER / PRIMARY DATA
      ↓
AUDIT TRAIL
      ↓
REPORTING
      ↓
REDUCTION / INSIGHT

CarbonTally should follow that conceptual model.

But we don't need to copy their UI or create a giant enterprise platform immediately.

2. The fundamental CarbonTally model

I want this principle frozen:

Source → Activity → Methodology → Factor → Calculation → Evidence → Review → Reporting

And:

Source document is not the same thing as an emissions activity.

For example:

Booking.com PDF
        ↓
Source
        ↓
Hotel booking
        ↓
Activity
        ↓
Hotel accommodation
        ↓
Scope 3 Category 6
        ↓
Methodology
        ↓
Factor
        ↓
Calculation

Likewise:

Uber receipt
        ↓
Taxi journey
        ↓
Business travel activity
        ↓
Category 6

And:

CSV employee survey
        ↓
commuting activity
        ↓
Category 7

This is critical because not every Scope 3 activity originates as a PDF invoice.

3. CarbonTally should support five ingestion channels

The specification should define these as first-class inputs.

A. Documents
PDF
image
scanned invoice
receipt
booking confirmation
statement
contract
shipping document
utility bill
supplier document
B. Structured files
CSV
XLSX
JSON
C. Integrations/API

Eventually:

ERP
accounting
expense management
travel management
procurement
utility providers
fleet systems
HR
supplier systems

Persefoni's current integrations demonstrate why this matters: Concur, Expensify and Navan can supply business-travel activity directly rather than forcing users to upload every receipt.

D. Supplier submissions
Supplier portal
Supplier questionnaire
PCF
EPD
supplier emissions statement
activity data
E. Manual entry
User knows:
12,500 kWh
3 hotel nights
1,500 passenger-km
2 tonnes waste

The calculation engine shouldn't care where the activity originated.

4. Canonical Activity model

This is one of the biggest things I want in the product specification.

Every source should eventually produce something conceptually like:

Activity
---------
activity_id
organization_id
source_document_id
source_line_item_id

scope
scope3_category

activity_type
activity_subtype

quantity
unit

origin
destination
country
region
facility

supplier_id
supplier_name
transaction_provider

activity_date
period_start
period_end

employee_id / anonymised subject
business_purpose

methodology
factor_id
factor_year

data_quality
estimation_status

evidence_id
review_status

performed_by
acting_for
data_owner

Not every field is populated for every activity.

Missing information stays missing.

5. Transaction provider vs actual supplier

This is a very important new requirement.

Example:

Booking.com
      ↓
Hotel ABC

Store:

transaction_provider = Booking.com
underlying_supplier = Hotel ABC
activity_type = hotel_accommodation

Similarly:

Trainline
      ↓
SNCB/CFL/etc.
Uber
      ↓
Taxi/private-hire activity
Expedia
      ↓
Airline

This prevents CarbonTally from confusing where someone purchased something with what generated the emissions.

6. Methodology hierarchy

CarbonTally needs an explicit methodology-selection engine.

I recommend:

1. Primary/supplier-specific emissions
             ↓
2. Product/activity-specific data
             ↓
3. Supplier-specific activity data
             ↓
4. Activity-based factor
             ↓
5. Average-data methodology
             ↓
6. Spend-based methodology
             ↓
7. Manual review / unresolved

But this must be category-specific.

We cannot make one universal hierarchy and assume it works for every category.

The GHG Protocol provides calculation methods for all 15 categories and guidance for choosing among methods.

The current UK government guidance also explicitly says activity-based factors should be used where available, while spend-based methods may be used where sufficient activity data isn't available, with the methodology reported.

Therefore:

Never silently convert missing activity data into invented activity data.

7. Data-quality model

Every activity should carry a quality classification.

For example:

PRIMARY
SUPPLIER_SPECIFIC
ACTIVITY_BASED
AVERAGE_DATA
SPEND_BASED
ESTIMATED
MANUAL
UNRESOLVED

And ideally a more granular data-quality score later.

Example:

Flight
London → Brussels
Economy
1 passenger

Excellent activity data.

Taxi
Uber
£42.80

No distance.

That's not equivalent quality.

CarbonTally should say:

Known:
transaction value

Missing:
distance / vehicle details

Method:
spend-based or manual-review pathway

Quality:
estimated
8. Scope 2 — complete product plan

GHG Protocol Scope 2 covers purchased/acquired:

electricity
steam
heating
cooling.

CarbonTally therefore needs four activity types:

electricity
heat
steam
cooling
Location-based

Model:

consumption
+
location/grid context
+
appropriate factor
=
Scope 2 location-based emissions

Example:

12,500 kWh
Dhaka office
2026 factor
Market-based

Model:

consumption
+
contractual instrument
+
allocation
+
eligibility
+
market-based factor
=
Scope 2 market-based emissions

Your P17 contractual-instrument work is therefore not optional decoration.

It needs to be visible in the complete model.

Evidence examples
utility invoice
meter data
supplier statement
energy contract
EAC/REC/REGO-type evidence where supported
contractual instrument
allocation evidence
supplier-specific factor
Scope 2 UI

Customer should see:

Scope 2
──────────────────
Location-based       XXX tCO2e
Market-based         XXX tCO2e

Electricity          XXX
Heat                 XXX
Steam                XXX
Cooling               XXX

And drill down:

Facility
↓
Energy activity
↓
Evidence
↓
Factor
↓
Method
↓
Calculation
↓
Review
9. Scope 3 — all 15 categories

The GHG Protocol defines 15 categories and states that companies report Scope 3 by category. The categories are designed to avoid double counting between categories.

CarbonTally should therefore have 15 explicit category contracts.

Category 1 — Purchased Goods & Services
Sources
supplier invoice
PO
procurement export
ERP
supplier PCF
EPD
supplier emissions statement
CSV
manual
Activity
product/service
quantity
unit
mass
spend
supplier
country
Methods
supplier-specific
hybrid
average-data
spend-based
Example
500 kg packaging
Supplier ABC
supplier PCF available

Prefer supplier-specific information.

If only:

£20,000 packaging spend

use an authorised spend methodology and mark quality accordingly.

10. Category 2 — Capital Goods

Sources:

asset invoice
ERP
fixed asset register
supplier PCF
EPD
procurement

Activity:

capital asset
quantity
mass/value
supplier
asset type

Need explicit capitalisation boundary.

This is one area where CarbonTally should never automatically classify every expensive purchase as Category 2.

11. Category 3 — Fuel & Energy Related Activities

This should connect strongly to Scope 1/2 activity.

Example:

10,000 kWh electricity

produces:

Scope 2 electricity

but associated upstream fuel/energy emissions can belong to:

Scope 3 Category 3

So the system needs a relationship:

source activity
      ↓
Scope 2 calculation
      +
Category 3 upstream calculation

with explicit double-counting controls.

12. Category 4 — Upstream Transportation & Distribution

Sources:

freight invoice
shipping manifest
carrier statement
logistics CSV
ERP
supplier data

Activity:

origin
destination
mode
mass
distance
shipment
tonne-km

Methods:

fuel-based
distance-based
spend-based
supplier-specific

Need boundary:

upstream transportation to the reporting organisation.

13. Category 5 — Waste Generated in Operations

This fits your existing waste work very well.

Input:

waste invoice
waste transfer note
supplier statement
weight record

Normalize:

material
quantity
route
treatment
supplier

Example:

500 kg cardboard
→ recycling

versus:

500 kg general waste
→ landfill

These must not become the same activity.

Your existing supplier-resolution and waste semantics work should become part of this contract.

14. Category 6 — Business Travel

This should become one of CarbonTally's flagship demonstrations.

Supported activity types:

air
rail
bus
taxi/private hire
rental car
personal car
hotel/accommodation
potentially other supported travel modes

Sources:

airline booking
Booking.com
Agoda
Expedia
Concur
Expensify
Navan
Trainline
rail operator
Uber
Bolt
taxi receipt
rental-car contract
rental-car invoice
hotel invoice
hotel booking
travel statement
CSV
manual

Persefoni's current integrations specifically demonstrate air, hotel, taxi, rail and rental-car activity as an integrated business-travel workflow.

Example journey
BUSINESS TRIP BT-2026-0042

UK
 ↓
✈ London → Brussels
 ↓
🏨 Brussels hotel × 1
 ↓
🚕 Taxi
 ↓
🚗 Rental car
 ↓
🚆 Brussels → Luxembourg
 ↓
🏨 Luxembourg hotel × 2
 ↓
✈ Luxembourg → UK

Seven activities.

One trip.

Seven auditable calculations.

One Category 6 aggregation.

This should be a canonical CarbonTally investor test journey.

15. Category 7 — Employee Commuting

Sources:

employee survey
HR data
travel survey
commuting app
public transport records
parking records
manual

Activity:

employee
home/work distance
days/year
mode
vehicle
occupancy

Example:

Employee 017
Dhaka → Office
18 km
car
3 days/week

Calculation:

distance
×
frequency
×
appropriate factor

Must support estimation because employee surveys will often be incomplete.

16. Category 8 — Upstream Leased Assets

Sources:

lease contracts
property records
utility bills
landlord data
asset data

Need to distinguish:

owned
leased
upstream/downstream

and avoid overlap with Scope 1/2.

17. Category 9 — Downstream Transportation & Distribution

Similar mechanics to Category 4 but opposite boundary.

The system must explicitly distinguish:

Cat 4 = upstream
Cat 9 = downstream

This is one of the mandatory double-counting controls.

18. Category 10 — Processing of Sold Products

Need activity information from downstream processors.

Sources:

customer data
supplier/customer questionnaire
processing statement
production data
industry-average data

Activity:

product
quantity
processing route
energy/process
location

This should not be represented as fully automated unless the required data exists.

19. Category 11 — Use of Sold Products

Need:

product
units sold
expected lifetime
energy/fuel consumption
use profile
geography

Potentially:

10,000 units
×
expected lifetime use
×
energy factor

This is methodology-heavy and should remain transparent.

20. Category 12 — End-of-Life Treatment

This should connect to your existing waste semantics.

But the boundary is different from Cat 5.

Cat 5:
waste generated by the reporting company's operations

Cat 12:
end-of-life treatment of products sold

That distinction needs an explicit invariant.

21. Category 13 — Downstream Leased Assets

Sources:

lease portfolio
tenant data
energy data
asset activity

Need:

leased asset
tenant
period
energy/activity
allocation

Boundary against Category 8 must be explicit.

22. Category 14 — Franchises

Sources:

franchise database
franchisee energy data
franchisee fuel data
supplier questionnaires
estimated activity

Need:

franchise
location
operational period
Scope 1/2 activity
allocation basis

This should have controlled estimation.

23. Category 15 — Investments

This deserves its own sub-system eventually.

Sources:

investment portfolio
investee emissions
financial data
PCAF-style data
annual reports
supplier/investee data

Activity:

investment
outstanding amount
ownership/equity share
enterprise value
emissions
asset class

Need:

investment methodology
allocation basis
data quality
source
reporting period

Do not treat this like a normal invoice category.

24. Cross-category boundary engine

This is absolutely essential.

We need explicit controls such as:

Cat 4 ↔ Cat 9
Cat 5 ↔ Cat 12
Cat 8 ↔ Cat 13
Scope 1/2 ↔ Cat 3
Scope 2 ↔ contractual instruments
Cat 1 ↔ Cat 2

The GHG Protocol itself emphasizes mutually exclusive categories and avoiding double counting.

CarbonTally should therefore have:

Boundary Check
     ↓
PASS
     OR
CLARIFICATION
     OR
BLOCK

Not merely a warning in the UI.

25. Evidence model

Every calculation should answer:

What did we receive?
PDF / CSV / API / manual / supplier
What did we extract?
12,500 kWh
What did we interpret it as?
Electricity consumption
Which scope/category?
Scope 2
Which methodology?
Location-based
Which factor?
Factor XYZ
2026
Which organisation owns the data?
Customer
Who performed the action?
Consultant user
Who were they acting for?
Customer organisation
What changed?
Calculation snapshot
Who reviewed it?
Reviewer

This fits directly into the P17 accounting/acting-for architecture you've already built.

26. Manual review is a feature, not an error

This needs to be explicit in the product specification.

Example:

Booking.com
£180
Brussels
1 night

Everything known.

Good.

But:

Uber
£42.80

No distance.

CarbonTally should show:

Needs review: activity distance unavailable.

Reviewer can:

provide distance
OR
approve spend-based methodology
OR
request evidence
OR
reject

That is much better than pretending automation is perfect.

27. Supplier workflow

Current competitors place considerable emphasis on supplier engagement and primary data. Normative, Watershed and Sweep all currently position supplier data collection/engagement as part of Scope 3 management.

CarbonTally should eventually support:

Customer
   ↓
Select supplier
   ↓
Request data
   ↓
Supplier receives request
   ↓
Supplier submits:
    PCF
    EPD
    emissions
    activity data
    methodology
    reporting period
   ↓
CarbonTally validates
   ↓
Reviewer approves
   ↓
Supplier-specific factor/data
   ↓
Calculation

This should coexist with estimated data.

28. Factor governance

This is another major product requirement.

For every calculation:

factor_id
factor_source
factor_year
factor_version
factor_scope
factor_category
factor_unit
factor_geography
factor_methodology

CarbonTally must never silently say:

"2026 factor unavailable, so we'll use 2025."

unless an explicit, approved fallback policy exists.

The current UK 2026 factor publication is particularly relevant because DESNZ publishes a full set, an automated flat file and methodology documentation, and even corrected the 2026 flat file in July 2026.

So factor ingestion itself needs:

source
version
publication date
effective/reporting year
checksum
supersession
29. Reporting model

The reporting layer should expose:

Scope 1
Scope 2 location-based
Scope 2 market-based
Scope 3
   Cat 1
   Cat 2
   ...
   Cat 15

But also:

Data quality
Methodology
Primary vs secondary
Estimated %
Manual-review %
Unresolved %
Evidence coverage

That is much more valuable than simply:

Total Scope 3 = 12,345 tCO2e.

The UK 2025–26 Sustainability Reporting Guidance currently uses a materiality-based approach for Scope 3 in the relevant public-sector framework and says partial Scope 3 coverage should identify the underlying categories.

So CarbonTally should preserve category-level transparency.

30. Investor dashboard

Eventually:

CARBON ACCOUNTING

FY2026
──────────────────────────

Scope 1              417.2 t
Scope 2 Location     821.4 t
Scope 2 Market       392.8 t
Scope 3            8,942.1 t

Scope 3 Coverage
──────────────────────────
Cat 1       2,102 t
Cat 2         810 t
Cat 3         430 t
...
Cat 15        321 t

Then:

Data Quality

Primary data             31%
Activity based            42%
Average data              18%
Spend based                7%
Estimated                  2%
Manual review              0%

Those percentages would be derived from actual data, not demo decoration.

31. Investor demo corpus

Now we can answer your original PDF question properly.

Don't generate:

15 PDFs because there are 15 categories.

Generate a representative evidence universe.

For example:

Scope 2
S2-01 Electricity invoice
S2-02 Heat invoice
S2-03 Cooling invoice
S2-04 Market-based contractual evidence
Scope 3
C1 supplier invoice + supplier PCF
C2 capital purchase
C3 electricity/fuel-linked activity
C4 freight document
C5 waste invoice
C6 complete business-trip bundle
C7 employee commuting dataset
C8 lease evidence
C9 downstream freight
C10 processing dataset
C11 product-use dataset
C12 end-of-life document
C13 downstream lease dataset
C14 franchise dataset
C15 investment portfolio dataset

Some are PDFs.

Some are CSV/XLSX.

Some are manual activities.

Some are supplier submissions.

Some intentionally produce manual review.

That is a realistic investor demo.

32. The flagship Category 6 demo

I would specifically freeze this as a canonical journey:

BT-2026-001
Employee business trip

London
 ↓
✈ Flight
 ↓
Brussels
 ↓
🏨 Hotel
 ↓
🚕 Taxi
 ↓
🚗 Rental car
 ↓
🚆 Train
 ↓
Luxembourg
 ↓
🏨 Hotel × 2
 ↓
✈ Flight
 ↓
London

Sources deliberately mixed:

Airline online PDF
Booking.com PDF
Uber PDF
Offline rental agreement PDF
Train ticket PDF
Agoda PDF
Return airline PDF

Then CarbonTally proves:

7 source documents
        ↓
7 activities
        ↓
7 calculations
        ↓
1 business trip
        ↓
1 Scope 3 Category 6 total

That would be an excellent investor demonstration.

33. P17 product maturity model

I would explicitly define:

Level 0 — Document captured
PDF exists
Level 1 — Extracted
fields extracted
Level 2 — Classified
scope/category/activity
Level 3 — Calculated
factor + calculation
Level 4 — Provenanced
source + factor + methodology + snapshot
Level 5 — Reviewed
human validation
Level 6 — Reportable
approved/reportable
Level 7 — Primary data
supplier-specific / actual data

This gives investors and internal teams a truthful understanding of maturity.

34. What I would NOT build yet

Even though competitors have these features, I would not immediately implement:

60+ external integrations
full supplier network
every travel provider API
automatic Booking.com API
automatic Agoda API
Uber API
Trainline API
every ERP
every procurement system
complete PCAF investment engine
full CSRD automation
every global emissions database
decarbonisation marketplace.

Those are future product expansion.

Instead, architect CarbonTally so they can plug into the canonical Activity model later.

35. What I would implement now

For CarbonTally's investor-ready stage:

Must have

Scope 2

electricity
heat
steam
cooling
location-based
market-based
contractual instrument
allocation
evidence
provenance
review
reporting

Scope 3

all 15 categories represented
at least one truthful calculation/estimation path per category
category-specific methodology
activity model
source/evidence
factor matching
data quality
estimation
manual review
supplier attribution
boundary controls
canonical persistence
audit trail
reportability lifecycle
Investor demo
synthetic organisation
realistic data
mixed ingestion
complete business-trip example
Scope 2 examples
all 15 categories
evidence viewer
calculation detail
review workflow
data-quality dashboard
reporting
Insight
36. The final PO architecture

This is the model I want Cline to build toward:

                         CARBONTALLY CAMS
                              │
              ┌───────────────┴───────────────┐
              │                               │
        DATA ACQUISITION                MASTER DATA
              │                               │
    ┌─────────┼─────────┐             ┌───────┼───────┐
    │         │         │             │       │       │
 Documents  Files      APIs        Factors Suppliers Orgs
    │         │         │
    └─────────┴─────────┘
              │
              ▼
        EXTRACTION
              │
              ▼
      NORMALISED ACTIVITY
              │
              ▼
       SCOPE CLASSIFIER
              │
       ┌──────┴──────┐
       │             │
    Scope 2       Scope 3
       │             │
   4 energy       15 categories
    types             │
       │              │
       └──────┬───────┘
              ▼
        METHODOLOGY
              │
              ▼
       FACTOR MATCHING
              │
              ▼
       CALCULATION ENGINE
              │
       ┌──────┴──────┐
       │             │
   DATA QUALITY   BOUNDARY
       │             │
       └──────┬──────┘
              ▼
        MANUAL REVIEW
              │
              ▼
        APPROVAL
              │
              ▼
       REPORTABLE DATA
              │
      ┌───────┼────────┐
      │       │        │
   Reports  Insight   Audit
37. My PO recommendation on the Cline report

Do not start P17-IMPLEMENT-09 yet.

First, send me the new Cline report you just received.

I'll then do a PO reconciliation:

Area	Cline delivered	Product requirement	Gap	Priority
Scope 2	—	complete contract	—	—
Cat 1	—	complete path	—	—
Cat 2	—	complete path	—	—
...	...	...	...	...
Cat 15	—	complete path	—	—
Evidence	—	source lineage	—	—
Methodology	—	category-specific	—	—
Data quality	—	explicit	—	—
Supplier	—	primary-data path	—	—
Review	—	controlled success	—	—
Reporting	—	category-level	—	—
Investor demo	—	realistic corpus	—	—
