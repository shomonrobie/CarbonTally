// frontend/src/public/glossaryData.js
// Local, self-contained glossary of carbon-accounting and emissions terms.
// Definitions follow established reference frameworks (GHG Protocol, IPCC,
// ISO 14064, UK SECR/ESOS/CSRD). Static reference content — no backend calls.

export const GLOSSARY_TERMS = [
  {
    term: 'Activity data',
    definition:
      'The quantitative measure of an activity that generates greenhouse gas emissions, such as litres of fuel, kilowatt-hours of electricity, miles travelled or tonnes of material.',
    category: 'Data & processing',
    example: '4,258.9 litres of diesel purchased in a month for a delivery fleet.',
    related: ['Emission factor', 'Normalisation'],
  },
  {
    term: 'Baseline year',
    definition:
      'The reference year against which an organisation measures changes in its greenhouse gas emissions over time. A baseline is recalculated when structural changes materially alter the boundary.',
    category: 'Reporting & compliance',
    example: 'Choosing FY2024 as the baseline against which net-zero progress is tracked.',
    related: ['Scope 1 emissions', 'Net zero'],
  },
  {
    term: 'Carbon dioxide equivalent (CO₂e)',
    definition:
      'A standard unit for comparing the climate impact of different greenhouse gases. Each gas is converted using its 100-year global warming potential so totals can be expressed as the equivalent amount of CO₂.',
    category: 'Units & factors',
    example: 'Methane (CH₄) has a GWP of 28, so 1 kg of CH₄ ≈ 28 kg CO₂e.',
    related: ['Global Warming Potential', 'Emission factor'],
  },
  {
    term: 'Carbon footprint',
    definition:
      'The total greenhouse gas emissions caused by an organisation, product or activity, usually expressed in tonnes of CO₂e over a defined period.',
    category: 'Emissions measurement',
    example: 'An SME reporting a 412 t CO₂e footprint across scopes 1 and 2 for the year.',
    related: ['Scope 1 emissions', 'Carbon intensity'],
  },
  {
    term: 'Carbon intensity',
    definition:
      'Emissions per unit of output or activity, such as kg CO₂e per £ of revenue, per tonne of product or per employee. Used to compare efficiency over time and between peers.',
    category: 'Units & factors',
    example: '0.18 kg CO₂e per £1 of revenue in 2025, down from 0.22 in 2024.',
    related: ['Carbon footprint', 'Normalisation'],
  },
  {
    term: 'Carbon neutral',
    definition:
      'A state in which emissions released are balanced by an equivalent amount removed from the atmosphere, typically through a combination of reductions and purchased offsets or removals.',
    category: 'Reduction & strategy',
    example: 'Claiming carbon neutrality for a single product line after offsetting residual emissions.',
    related: ['Net zero', 'Carbon offset'],
  },
  {
    term: 'Carbon offset',
    definition:
      'A reduction or removal of emissions elsewhere that an organisation purchases to compensate for emissions it cannot yet eliminate, usually through verified projects.',
    category: 'Reduction & strategy',
    example: 'Purchasing verified credits from an afforestation project to cover business travel.',
    related: ['Carbon credit', 'Net zero'],
  },
  {
    term: 'Carbon Reduction Plan',
    definition:
      'A document required under UK public procurement rules (PPN 06/21) in which suppliers set out their organisational emissions, a net-zero commitment and the steps they will take to reduce them.',
    category: 'Reporting & compliance',
    example: 'A supplier publishing its Carbon Reduction Plan to bid for a public-sector contract.',
    related: ['SECR', 'Net zero'],
  },
  {
    term: 'CSRD',
    definition:
      'The EU Corporate Sustainability Reporting Directive, which requires in-scope companies to report material sustainability information, including greenhouse gas emissions, under the European Sustainability Reporting Standards (ESRS).',
    category: 'Reporting & compliance',
    example: 'A large EU parent requiring subsidiaries to provide scope 1–3 data for consolidated CSRD reporting.',
    related: ['Scope 3 emissions', 'ESOS'],
  },
  {
    term: 'Data quality',
    definition:
      'How fit emissions data is for its purpose, judged by attributes such as accuracy, completeness, timeliness and traceability. Poor data quality is the main source of rework in carbon accounting.',
    category: 'Data & processing',
    example: 'Rating an invoice-derived fuel figure higher than an estimated one because it is measured, not extrapolated.',
    related: ['Activity data', 'Data validation'],
  },
  {
    term: 'Data validation',
    definition:
      'The process of checking data against defined rules — formats, ranges, consistency and completeness — before it is accepted into a calculation pipeline.',
    category: 'Data & processing',
    example: 'Flagging a transaction whose fuel volume exceeds the tank capacity of the declared vehicle.',
    related: ['Data quality', 'Normalisation'],
  },
  {
    term: 'Emission factor',
    definition:
      'A coefficient that converts activity data into greenhouse gas emissions, usually expressed as kg CO₂e per unit (litre, kWh, tonne, km). Factors are published by bodies such as the UK Government (DEFRA/UK GHG Conversion Factors), the IEA and the EPA.',
    category: 'Units & factors',
    example: 'DEFRA factor for diesel (average biofuel blend): 2.52 kg CO₂e per litre.',
    related: ['Activity data', 'Carbon dioxide equivalent (CO₂e)'],
  },
  {
    term: 'ESOS',
    definition:
      'The UK Energy Savings Opportunity Scheme, a mandatory energy-assessment scheme for large undertakings. Participants must identify cost-effective energy-saving opportunities every four years.',
    category: 'Reporting & compliance',
    example: 'A large company carrying out an ESOS assessment and reporting its findings to the Environment Agency.',
    related: ['SECR', 'Carbon Reduction Plan'],
  },
  {
    term: 'GHG Protocol',
    definition:
      'The most widely used international standard for corporate greenhouse gas accounting, providing guidance on boundaries, scope classification and calculation methods used by most reporting frameworks.',
    category: 'Standards & frameworks',
    example: 'Structuring a corporate inventory into scope 1, 2 and 3 categories following the GHG Protocol Corporate Standard.',
    related: ['Scope 1 emissions', 'Operational boundary'],
  },
  {
    term: 'Global Warming Potential (GWP)',
    definition:
      'A factor that expresses the warming effect of a greenhouse gas relative to CO₂ over a chosen time horizon (usually 100 years). It is used to convert gas emissions into CO₂e.',
    category: 'Units & factors',
    example: 'Using the AR6 100-year GWP of 29.8 for methane when converting to CO₂e.',
    related: ['Carbon dioxide equivalent (CO₂e)', 'Emission factor'],
  },
  {
    term: 'Greenhouse gas (GHG)',
    definition:
      'A gas that traps heat in the atmosphere. The gases covered by the UNFCCC/Kyoto Protocol are carbon dioxide (CO₂), methane (CH₄), nitrous oxide (N₂O), hydrofluorocarbons, perfluorocarbons, sulphur hexafluoride and nitrogen trifluoride.',
    category: 'Emissions measurement',
    example: 'Accounting for CO₂, CH₄ and N₂O from a fleet and heating systems.',
    related: ['Carbon dioxide equivalent (CO₂e)', 'Scope 1 emissions'],
  },
  {
    term: 'ISO 14064',
    definition:
      'An international standard for quantifying and reporting greenhouse gas emissions and removals at organisational and project level, including requirements for verification.',
    category: 'Standards & frameworks',
    example: 'Having a third party verify an organisation’s emissions report to ISO 14064-3.',
    related: ['GHG Protocol', 'Verified'],
  },
  {
    term: 'Life-cycle assessment (LCA)',
    definition:
      'A method for assessing the environmental impacts of a product or service across its full life cycle — raw materials, production, use and end of life.',
    category: 'Standards & frameworks',
    example: 'Comparing the cradle-to-grave emissions of two packaging materials.',
    related: ['Scope 3 emissions', 'Upstream / downstream'],
  },
  {
    term: 'Market-based / location-based',
    definition:
      'Two methods for calculating scope 2 electricity emissions. Location-based uses the average grid intensity of the region where consumption occurs; market-based reflects the specific electricity products purchased (such as renewable tariffs or Energy Attribute Certificates).',
    category: 'Emissions measurement',
    example: 'Reporting location-based emissions of 0.21 kg CO₂e/kWh alongside market-based emissions of 0.02 kg CO₂e/kWh on a renewable tariff.',
    related: ['Scope 2 emissions', 'Renewable energy'],
  },
  {
    term: 'Materiality',
    definition:
      'The principle that reporting should cover the emissions sources that matter. A source is material if omitting or misstating it could influence decisions made on the basis of the report.',
    category: 'Reporting & compliance',
    example: 'Omitting a negligible occasional hire vehicle while reporting all regular fleet fuel.',
    related: ['Operational boundary', 'Scope 3 emissions'],
  },
  {
    term: 'Net zero',
    definition:
      'A science-based target to cut emissions to as close to zero as possible, with any residual emissions balanced by durable removals. Often aligned to the Science Based Targets initiative (SBTi) criteria.',
    category: 'Reduction & strategy',
    example: 'Committing to net-zero greenhouse gas emissions across the value chain by 2050.',
    related: ['Carbon neutral', 'SBTi', 'Carbon offset'],
  },
  {
    term: 'Normalisation',
    definition:
      'The practice of dividing emissions by a business metric so that performance can be compared fairly across time, sites or peers.',
    category: 'Data & processing',
    example: 'Reporting kg CO₂e per full-time employee to compare two divisions of different size.',
    related: ['Carbon intensity', 'Data quality'],
  },
  {
    term: 'Operational boundary',
    definition:
      'The choice of which scope 1, 2 and 3 emissions to include in an inventory, made after setting the organisational boundary.',
    category: 'Emissions measurement',
    example: 'Deciding to include scope 3 category 6 (business travel) from year one.',
    related: ['Scope 3 emissions', 'Organisational boundary'],
  },
  {
    term: 'Organisational boundary',
    definition:
      'The definition of which entities, sites and operations belong to the reporting organisation, using either the control approach (financial or operational) or the equity-share approach.',
    category: 'Emissions measurement',
    example: 'Consolidating a 51%-owned subsidiary under the operational control approach.',
    related: ['Operational boundary', 'Scope 1 emissions'],
  },
  {
    term: 'Renewable energy',
    definition:
      'Energy generated from sources that are naturally replenished, such as wind, solar, hydro and biomass. Purchasing renewable electricity can lower market-based scope 2 emissions.',
    category: 'Reduction & strategy',
    example: 'Signing a renewable power purchase agreement (PPA) for a manufacturing site.',
    related: ['Scope 2 emissions', 'Market-based / location-based'],
  },
  {
    term: 'SBTi',
    definition:
      'The Science Based Targets initiative, which independently assesses whether corporate emission-reduction targets align with the goals of the Paris Agreement.',
    category: 'Standards & frameworks',
    example: 'Submitting a near-term scope 1 and 2 target for validation by the SBTi.',
    related: ['Net zero', 'Scope 3 emissions'],
  },
  {
    term: 'Scope 1 emissions',
    definition:
      'Direct greenhouse gas emissions from sources an organisation owns or controls: fuel burned on site, company vehicles, and fugitive refrigerant and process emissions.',
    category: 'Emissions measurement',
    example: 'Diesel used by a company-owned delivery fleet.',
    related: ['Scope 2 emissions', 'GHG Protocol'],
  },
  {
    term: 'Scope 2 emissions',
    definition:
      'Indirect emissions from the generation of purchased electricity, steam, heating and cooling consumed by the organisation.',
    category: 'Emissions measurement',
    example: 'Electricity purchased from the grid to power an office building.',
    related: ['Scope 1 emissions', 'Market-based / location-based'],
  },
  {
    term: 'Scope 3 emissions',
    definition:
      'All other indirect emissions in an organisation’s value chain, split into 15 categories such as purchased goods and services, upstream transport, business travel, and use of sold products.',
    category: 'Emissions measurement',
    example: 'Emissions from suppliers producing the raw materials an organisation buys.',
    related: ['Scope 1 emissions', 'Upstream / downstream', 'Materiality'],
  },
  {
    term: 'SECR',
    definition:
      'The UK Streamlined Energy and Carbon Reporting framework, which requires large companies to report their UK energy use, scope 1 and 2 emissions and an intensity metric in their annual reports.',
    category: 'Reporting & compliance',
    example: 'A large company including its SECR-qualifying emissions in the directors’ report.',
    related: ['ESOS', 'Carbon Reduction Plan', 'Carbon intensity'],
  },
  {
    term: 'Upstream / downstream',
    definition:
      'Terms describing where in the value chain a scope 3 source sits. Upstream covers suppliers and inputs; downstream covers distribution, use and end of life of products.',
    category: 'Emissions measurement',
    example: 'Upstream: raw materials. Downstream: customers’ use of sold products.',
    related: ['Scope 3 emissions', 'Life-cycle assessment (LCA)'],
  },
  {
    term: 'Verified',
    definition:
      'The outcome of an independent, impartial assessment of an emissions report against a standard, confirming that data, methods and disclosures are accurate and complete.',
    category: 'Reporting & compliance',
    example: 'An accountant providing a limited assurance opinion on a client’s emissions statement.',
    related: ['ISO 14064', 'Data quality'],
  },
];
