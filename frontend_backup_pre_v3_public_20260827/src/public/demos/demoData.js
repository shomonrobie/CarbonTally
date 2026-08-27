// frontend/src/public/demos/demoData.js
// FABRICATED demo data only — no customer data, no real invoices, no real
// people, no production identifiers. The demos tell one small coherent story:
// a fictional food business ("Aurora Foods") submits a fictional diesel invoice
// which flows through extraction -> mapping -> calculation -> review -> evidence
// -> dashboard. Every figure below is invented for demonstration.
export const COMPANY = 'Aurora Foods Ltd';

export const INVOICE = {
  supplier: 'Meridian Fuel Supplies Ltd',
  ref: 'INV-2026-0417',
  date: '06 Mar 2026',
  site: 'Birmingham Hub',
  item: 'Red diesel',
  qty: '4,258.9',
  unit: 'litres',
  amount: '£9,845.20',
  page: 1,
};

// Raw messy source line as it might appear on the document.
export const RAW_LINE =
  'MERIDIAN FUEL SUPPLIES  RED DIESEL 06-03-26  4258.9 L  £9,845.20';

export const FACTOR = {
  name: 'Gas oil (red diesel)',
  provider: 'DEFRA',
  year: 2026,
  unit: 'litres',
  rate: 2.52, // kg CO2e per litre (illustrative factor)
  method: 'Quantity × emission factor',
};

export const RESULT = {
  kg: 10732.4, // 4258.9 × 2.52
  tonnes: 10.7,
};

// Candidate factors for the mapping demo, in order of appearance.
export const CANDIDATE_FACTORS = [
  {
    name: 'Gas oil (red diesel)',
    source: 'DEFRA 2026',
    rate: '2.52 kg CO₂e / litre',
    method: 'Exact match — activity & unit',
    confidence: 0.98,
    selected: true,
  },
  {
    name: 'Diesel (average biofuel blend)',
    source: 'DEFRA 2026',
    rate: '2.52 kg CO₂e / litre',
    method: 'Similar fuel — different blend',
    confidence: 0.77,
    selected: false,
  },
  {
    name: 'Diesel (100% mineral)',
    source: 'DEFRA 2026',
    rate: '2.61 kg CO₂e / litre',
    method: 'Different fuel blend',
    confidence: 0.71,
    selected: false,
  },
  {
    name: 'Gas oil (red diesel)',
    source: 'DEFRA 2025',
    rate: '2.51 kg CO₂e / litre',
    method: 'Prior-year factor',
    confidence: 0.66,
    selected: false,
  },
];

export const WHY_FACTOR_SELECTED =
  'Closest activity and unit match, current-year factor (DEFRA 2026), within the approved factor set. Every candidate and its score is kept so the choice can be explained.';

// Fields detected by extraction (document demo), in display order.
export const EXTRACTED_FIELDS = [
  { label: 'Supplier', value: 'Meridian Fuel Supplies Ltd', confidence: 0.99 },
  { label: 'Invoice number', value: 'INV-2026-0417', confidence: 0.98 },
  { label: 'Date', value: '06 Mar 2026', confidence: 0.97 },
  { label: 'Fuel / activity', value: 'Red diesel — described as "RED DIESEL"', confidence: 0.89 },
  { label: 'Quantity', value: '4,258.9', confidence: 0.91 },
  { label: 'Unit', value: 'litres', confidence: 0.93 },
  { label: 'Location', value: 'Birmingham Hub', confidence: 0.85 },
  { label: 'Reference', value: 'Delivery note 3021', confidence: 0.95 },
];

// Validation findings for the human-review demo (mirror real validation rules:
// quantity, unit, activity, year).
export const REVIEW_FINDINGS = [
  {
    level: 'warning',
    title: 'Quantity unit is inconsistent in the source',
    detail: 'Document mixes "L" and "litres". Reviewer confirmed litres.',
  },
  {
    level: 'warning',
    title: 'Activity description is abbreviated',
    detail: 'Source says "RED DIESEL"; recorded as Red diesel (gas oil) for mapping.',
  },
  {
    level: 'info',
    title: 'Reporting year inferred',
    detail: 'Taken from the invoice date (2026).',
  },
];

export const REVIEW_CHECKS = [
  { label: 'Quantity', detail: '4,258.9 litres confirmed' },
  { label: 'Fuel', detail: 'Red diesel confirmed' },
  { label: 'Date', detail: '06 Mar 2026 confirmed' },
  { label: 'Supplier', detail: 'New supplier — verified' },
];

// Evidence chain (mirrors the D33.1 evidence record: source document ->
// extracted line -> emission factor -> calculation -> emission result).
export const EVIDENCE_CHAIN = [
  { icon: '🧾', title: 'Source document', detail: 'Meridian Fuel Supplies Ltd — invoice INV-2026-0417, page 1' },
  { icon: '📄', title: 'Extracted line', detail: 'Line 2 — 4,258.9 litres Red diesel' },
  { icon: '⚖️', title: 'Emission factor', detail: 'DEFRA 2026 — Gas oil (red diesel) — 2.52 kg CO₂e / litre' },
  { icon: '🧮', title: 'Calculation', detail: '4,258.9 litres × 2.52 kg CO₂e / litre — snapshot v1.0 (reproducible)' },
  { icon: '📊', title: 'Emission result', detail: '10,732.4 kg CO₂e (≈ 10.7 t CO₂e)' },
];

// ===========================================================================
// FULL-WORKSPACE DEMO DATA (fabricated, deterministic, local-only)
// ---------------------------------------------------------------------------
// Two fictional Customer Organisations (Aurora Foods Ltd, Beacon Textiles Ltd)
// plus a third for the consultant view (Trent Logistics Ltd). Each org carries
// a small, internally-consistent dataset: emissions summary, processing
// pipeline, documents, processing work, factors, reports, team. The work items
// reuse the same narrative structure as demos A–F (document -> extracted line
// -> factor -> calculation -> evidence -> result). Nothing here is real.
// ===========================================================================

export const WORKFLOW_STEPS = [
  { id: 'document', label: 'Document' },
  { id: 'extracted', label: 'Extracted data' },
  { id: 'factor', label: 'Emission factor' },
  { id: 'calculation', label: 'Calculation' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'result', label: 'Result' },
];

const INVOICE_DOC = {
  format: 'PDF (scanned)',
  supplier: 'Meridian Fuel Supplies Ltd',
  ref: 'INV-2026-0417',
  date: '06 Mar 2026',
  site: 'Birmingham Hub',
  page: 1,
};

const GAS_BILL_DOC = {
  format: 'PDF (electronic)',
  supplier: 'Scottish Power Energy Retail',
  ref: 'G-2210',
  date: '12 Feb 2026',
  site: 'Leeds Mill',
  page: 1,
};

const FLEET_DOC = {
  format: 'Spreadsheet (XLSX)',
  supplier: 'Fleet card statement — Trent Logistics',
  ref: 'FC-Q1-2026',
  date: '31 Mar 2026',
  site: 'Nottingham Depot',
  page: 1,
};

// One shared work-item "pack" generator so every item has the same structure.
function workItem({
  id, batch, title, items, status, assigned, doc, line, factor, qty, calc,
  resultKg, snapshot, findings = [], confidence = 0.92,
}) {
  return {
    id, batch, title, items, status, assigned,
    doc,
    extracted: {
      line,
      fields: [
        { label: 'Supplier', value: doc.supplier, confidence: 0.98 },
        { label: 'Reference', value: doc.ref, confidence: 0.99 },
        { label: 'Date', value: doc.date, confidence: 0.97 },
        { label: 'Activity', value: line.activity, confidence },
        { label: 'Quantity', value: line.qty, confidence: 0.91 },
        { label: 'Unit', value: line.unit, confidence: 0.93 },
        { label: 'Location', value: doc.site, confidence: 0.85 },
      ],
    },
    factor,
    calc,
    result: {
      kg: resultKg,
      tonnes: Math.round(resultKg / 1000 * 10) / 10,
      snapshot,
    },
    findings,
  };
}

const WORK_ITEM_DIESEL = workItem({
  id: 'w-aurora-1',
  batch: 'B-1042',
  title: 'Q1 2026 fuel & utility invoices',
  items: 24,
  status: 'customer_review',
  assigned: 'CarbonTally specialists',
  doc: INVOICE_DOC,
  line: { activity: 'Red diesel', qty: '4,258.9', unit: 'litres' },
  factor: { name: 'Gas oil (red diesel)', provider: 'DEFRA', year: 2026, unit: 'litres', rate: 2.52 },
  calc: '4,258.9 litres × 2.52 kg CO₂e / litre',
  resultKg: 10732.4,
  snapshot: 'SNAP-2026-0177 · v1.0',
  confidence: 0.89,
  findings: [
    { level: 'warning', title: 'Quantity unit is inconsistent in the source', detail: 'Document mixes "L" and "litres". Reviewer confirmed litres.' },
    { level: 'warning', title: 'Activity description is abbreviated', detail: 'Source says "RED DIESEL"; recorded as Red diesel (gas oil) for mapping.' },
    { level: 'info', title: 'Reporting year inferred', detail: 'Taken from the invoice date (2026).' },
  ],
});

const WORK_ITEM_GAS = workItem({
  id: 'w-beacon-1',
  batch: 'B-1109',
  title: 'Jan–Mar 2026 utility bills',
  items: 9,
  status: 'approved',
  assigned: 'CarbonTally specialists',
  doc: GAS_BILL_DOC,
  line: { activity: 'Natural gas (gross CV)', qty: '61,850', unit: 'kWh' },
  factor: { name: 'Natural gas (gross CV)', provider: 'DEFRA', year: 2026, unit: 'kWh', rate: 0.18385 },
  calc: '61,850 kWh × 0.18385 kg CO₂e / kWh',
  resultKg: 11370.9,
  snapshot: 'SNAP-2026-0211 · v1.0',
  confidence: 0.97,
  findings: [
    { level: 'info', title: 'Units confirmed', detail: 'Bill reports kWh; factor set applies gross CV.' },
    { level: 'info', title: 'Reporting year inferred', detail: 'Taken from the billing period (Q1 2026).' },
  ],
});

const WORK_ITEM_FLEET = workItem({
  id: 'w-trent-1',
  batch: 'B-1155',
  title: 'Q1 2026 fleet fuel',
  items: 41,
  status: 'mapping',
  assigned: 'CarbonTally specialists',
  doc: FLEET_DOC,
  line: { activity: 'Diesel (road)', qty: '12,400', unit: 'litres' },
  factor: { name: 'Diesel (average biofuel blend)', provider: 'DEFRA', year: 2026, unit: 'litres', rate: 2.52 },
  calc: '12,400 litres × 2.52 kg CO₂e / litre',
  resultKg: 31248,
  snapshot: 'pending',
  confidence: 0.9,
  findings: [
    { level: 'warning', title: 'Split by vehicle class', detail: 'Statement mixes HGV and van mileage; awaiting allocation.' },
  ],
});

export const WORKSPACES = [
  {
    id: 'aurora',
    name: 'Aurora Foods Ltd',
    tag: 'Food manufacturing · Birmingham, UK',
    period: 'Jan – Jun 2026',
    total: 128.0,
    scopes: [
      { name: 'Scope 1', value: 42.6, note: 'Owned fuel & gas' },
      { name: 'Scope 2', value: 18.3, note: 'Purchased electricity' },
      { name: 'Scope 3', value: 67.1, note: 'Supply chain & travel' },
    ],
    records: 1284,
    verified: 1203,
    flagged: 81,
    inReview: 14,
    pipeline: [
      { stage: 'Extraction', count: 0 },
      { stage: 'Mapping', count: 0 },
      { stage: 'Validation', count: 8 },
      { stage: 'Customer review', count: 14 },
      { stage: 'Approved', count: 1262 },
    ],
    documents: [
      { name: 'Meridian Fuel Supplies — INV-2026-0417', type: 'PDF (scanned)', pages: 1, status: 'Extracted' },
      { name: 'Utility bill — Jan 2026', type: 'PDF (electronic)', pages: 3, status: 'Approved' },
      { name: 'Fleet mileage return — Q1', type: 'Spreadsheet (XLSX)', pages: 2, status: 'In review' },
      { name: 'Delivery notes — March', type: 'PDF (scanned)', pages: 8, status: 'Extracted' },
    ],
    workItems: [WORK_ITEM_DIESEL],
    factors: [
      { name: 'DEFRA 2026 (in use)', note: '7,029 validated factors · current year' },
      { name: 'SEAI 2025 (Irish)', note: 'Available for Irish operations' },
      { name: 'Custom factors', note: 'Customer-approved, auditable' },
    ],
    reports: [
      { name: 'FY2026 interim emissions report', status: 'Draft', date: 'In progress' },
      { name: 'Q1 2026 verified extract', status: 'Completed', date: '07 Apr 2026' },
    ],
    team: [
      { name: 'Amara Osei', role: 'Owner', email: 'amara@aurorafoods.example' },
      { name: 'Danny Cole', role: 'Admin', email: 'danny@aurorafoods.example' },
      { name: 'Priya Shah', role: 'Member', email: 'priya@aurorafoods.example' },
      { name: 'Tom Vickers', role: 'Viewer', email: 'tom@aurorafoods.example' },
    ],
  },
  {
    id: 'beacon',
    name: 'Beacon Textiles Ltd',
    tag: 'Textile manufacturing · Leeds, UK',
    period: 'Jan – Mar 2026',
    total: 46.2,
    scopes: [
      { name: 'Scope 1', value: 19.8, note: 'Natural gas & owned fuel' },
      { name: 'Scope 2', value: 21.4, note: 'Purchased electricity' },
      { name: 'Scope 3', value: 5.0, note: 'Waste & upstream' },
    ],
    records: 312,
    verified: 288,
    flagged: 14,
    inReview: 10,
    pipeline: [
      { stage: 'Extraction', count: 0 },
      { stage: 'Mapping', count: 2 },
      { stage: 'Validation', count: 4 },
      { stage: 'Customer review', count: 10 },
      { stage: 'Approved', count: 296 },
    ],
    documents: [
      { name: 'Scottish Power — G-2210', type: 'PDF (electronic)', pages: 2, status: 'Approved' },
      { name: 'Electricity bill — Feb 2026', type: 'PDF (electronic)', pages: 2, status: 'Approved' },
      { name: 'Waste transfer notes — Q1', type: 'PDF (scanned)', pages: 6, status: 'In review' },
    ],
    workItems: [WORK_ITEM_GAS],
    factors: [
      { name: 'DEFRA 2026 (in use)', note: 'Current-year UK factors' },
      { name: 'Custom factors', note: 'Supplier-specific electricity' },
    ],
    reports: [
      { name: 'Q1 2026 emissions report', status: 'Completed', date: '20 Apr 2026' },
    ],
    team: [
      { name: 'Laura Nguyen', role: 'Owner', email: 'laura@beacontextiles.example' },
      { name: 'Imran Ali', role: 'Admin', email: 'imran@beacontextiles.example' },
    ],
  },
  {
    id: 'trent',
    name: 'Trent Logistics Ltd',
    tag: 'Road transport · Nottingham, UK',
    period: 'Jan – Mar 2026',
    total: 61.8,
    scopes: [
      { name: 'Scope 1', value: 44.9, note: 'Fleet diesel' },
      { name: 'Scope 2', value: 9.2, note: 'Depot electricity' },
      { name: 'Scope 3', value: 7.7, note: 'Subcontracted haulage' },
    ],
    records: 540,
    verified: 466,
    flagged: 31,
    inReview: 24,
    pipeline: [
      { stage: 'Extraction', count: 0 },
      { stage: 'Mapping', count: 41 },
      { stage: 'Validation', count: 12 },
      { stage: 'Customer review', count: 24 },
      { stage: 'Approved', count: 463 },
    ],
    documents: [
      { name: 'Fleet card statement — Q1 2026', type: 'Spreadsheet (XLSX)', pages: 9, status: 'In review' },
      { name: 'Depot electricity — Mar 2026', type: 'PDF (electronic)', pages: 2, status: 'Approved' },
    ],
    workItems: [WORK_ITEM_FLEET],
    factors: [
      { name: 'DEFRA 2026 (in use)', note: 'Fuel & HGV factors' },
    ],
    reports: [
      { name: 'Q1 2026 fleet emissions', status: 'In progress', date: 'Draft' },
    ],
    team: [
      { name: 'Sofia Brandt', role: 'Owner', email: 'sofia@trentlogistics.example' },
      { name: 'Ryan Shaw', role: 'Member', email: 'ryan@trentlogistics.example' },
    ],
  },
];

// The consultant's fictional firm and its client relationships. Client access
// follows the CarbonTally role model: an ACTIVE client grant is the source of
// access; suspended clients lose access at the platform and database levels.
export const CONSULTANT = {
  firm: 'Net Zero Advisory Ltd',
  partner: 'Elena Marchetti',
  clients: [
    { id: 'aurora', name: 'Aurora Foods Ltd', status: 'active', emissions: 128.0, progress: 86, reviews: 3, dataQuality: 94, recent: 'Q1 2026 fuel & utility invoices' },
    { id: 'beacon', name: 'Beacon Textiles Ltd', status: 'active', emissions: 46.2, progress: 97, reviews: 0, dataQuality: 99, recent: 'Jan–Mar 2026 utility bills' },
    { id: 'trent', name: 'Trent Logistics Ltd', status: 'suspended', emissions: 61.8, progress: 71, reviews: 6, dataQuality: 86, recent: 'Q1 2026 fleet fuel' },
  ],
};

// Dashboard demo (fictional Aurora Foods footprint, Jan–Jun 2026).
export const DASHBOARD = {
  company: 'Aurora Foods Ltd',
  period: 'Jan – Jun 2026',
  scopes: [
    { name: 'Scope 1', value: 42.6, note: 'Owned fuel & gas' },
    { name: 'Scope 2', value: 18.3, note: 'Purchased electricity' },
    { name: 'Scope 3', value: 67.1, note: 'Supply chain & travel' },
  ],
  total: 128.0,
  records: 1284,
  verified: 1203,
  flagged: 81,
  categories: [
    { name: 'Diesel (road)', value: 38.2 },
    { name: 'Business travel', value: 31.6 },
    { name: 'Waste', value: 21.2 },
    { name: 'Natural gas', value: 18.7 },
    { name: 'Electricity', value: 18.3 },
  ],
  trend: [
    { month: 'Jan', value: 24.1 },
    { month: 'Feb', value: 22.6 },
    { month: 'Mar', value: 21.9 },
    { month: 'Apr', value: 20.8 },
    { month: 'May', value: 20.1 },
    { month: 'Jun', value: 18.5 },
  ],
};
