// frontend/src/v3/__tests__/capability-truth-surface.test.jsx
// P17-L — the governed capability truth surface (customer + product/investor).
//
// These tests pin the gates a *rendered* surface must satisfy
// (CT-PO-P17-DECISION-03 §18.3), now that a surface exists:
//
//   AG-3  no Axis-A token (`PARTIAL`/`DEFERRED`/`NOT_IMPLEMENTED`) is rendered
//   AG-4  no placeholder, no zero and no fabricated figure for a non-produced item
//   AG-5  the product/investor surface renders no tenant identifier and opens no
//         tenant query path
//   AG-6  both surfaces render the SAME governed value for the same requirement
//   AG-7  the four-way rollup is shown, and never a total
//   AG-8  every claim shows provenance or an explicit unresolved-source marker
//
// The surfaces own no capability truth: the fixture below is exactly the shape
// the canonical projection returns, and the assertions check that the rendered
// text is what the payload said — never something the frontend invented.
import React from 'react';
import { render, screen, cleanup, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import fs from 'fs';
import path from 'path';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: jest.fn(), getUser: jest.fn() } },
}));

jest.mock('../api', () => ({
  getCapabilityCatalogue: jest.fn(),
}));

import CapabilitiesPage from '../capabilities/CapabilitiesPage';
import InvestorCapabilityPage from '../capabilities/InvestorCapabilityPage';

const api = jest.requireMock('../api');

const VOCABULARY = [
  'SUPPORTED',
  'PARTIALLY_SUPPORTED',
  'STRUCTURED_INPUT_REQUIRED',
  'EXTERNAL_INPUT_REQUIRED',
  'MISSING_CAPABILITY',
  'FUTURE',
  'NOT_APPLICABLE_TO_PRODUCT',
];

const EXPLANATION = {
  SUPPORTED: 'CarbonTally supports this requirement, within the defined acceptance path.',
  PARTIALLY_SUPPORTED:
    'CarbonTally supports this requirement within a bounded scope. The scope, and what lies outside it, are stated on the requirement itself.',
  MISSING_CAPABILITY:
    'CarbonTally does not currently support this requirement. It requires the prerequisite named on the requirement.',
  FUTURE:
    'CarbonTally has not yet delivered this requirement. It is pending the named decision or prerequisite recorded on the requirement, and no value is produced for it today.',
  STRUCTURED_INPUT_REQUIRED:
    'CarbonTally supports this requirement, but producing a value depends on the required structured input being supplied.',
  EXTERNAL_INPUT_REQUIRED:
    'CarbonTally supports this requirement, but producing a value depends on the required external input being supplied.',
  NOT_APPLICABLE_TO_PRODUCT:
    "This requirement is not the product's own to produce. It is a statement about the product and never a statement about any customer.",
};

// The frozen `M-1` image (`DECISION-03 §11.1`/`§11.2`) — 4 / 6 / 3 / 2.
const M1_IMAGE = {
  'GP-S3-CAT-01': 'PARTIALLY_SUPPORTED',
  'GP-S3-CAT-02': 'MISSING_CAPABILITY',
  'GP-S3-CAT-03': 'SUPPORTED',
  'GP-S3-CAT-04': 'SUPPORTED',
  'GP-S3-CAT-05': 'SUPPORTED',
  'GP-S3-CAT-06': 'SUPPORTED',
  'GP-S3-CAT-07': 'PARTIALLY_SUPPORTED',
  'GP-S3-CAT-08': 'PARTIALLY_SUPPORTED',
  'GP-S3-CAT-09': 'PARTIALLY_SUPPORTED',
  'GP-S3-CAT-10': 'MISSING_CAPABILITY',
  'GP-S3-CAT-11': 'FUTURE',
  'GP-S3-CAT-12': 'PARTIALLY_SUPPORTED',
  'GP-S3-CAT-13': 'PARTIALLY_SUPPORTED',
  'GP-S3-CAT-14': 'FUTURE',
  'GP-S3-CAT-15': 'FUTURE',
};

const ROLLUP = {
  SUPPORTED: 4,
  PARTIALLY_SUPPORTED: 6,
  FUTURE: 3,
  MISSING_CAPABILITY: 2,
};

const UNRESOLVED = 'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION';

function requirement(code, capability, extra = {}) {
  return {
    requirement_code: code,
    requirement_name: `Requirement ${code}`,
    framework_code: 'GHG_PROTOCOL',
    framework_version_label: 'Corporate Accounting and Reporting Standard (2004 revised edition)',
    scope: extra.scope || 'Scope 3',
    scope2_method: extra.scope2_method || null,
    scope3_category: extra.scope3_category === undefined ? null : extra.scope3_category,
    carbontally_capability: capability,
    capability_explanation: EXPLANATION[capability],
    requirement_class: extra.requirement_class || 'CONDITIONAL',
    requirement_class_expression: extra.requirement_class_expression || 'CONDITIONAL',
    supported: extra.supported === undefined ? capability !== 'MISSING_CAPABILITY' : extra.supported,
    provenance: {
      source_locator: 'GHG Protocol Corporate Value Chain (Scope 3) Standard',
      authoritative_text_ref: 'verified 2026-09-12 (source tier 1)',
      source_tier: 1,
      official_identifier: null,
      identifier_status: UNRESOLVED,
    },
    capability_detail: 'Bounded scope. Prerequisite: the named prerequisite.',
    result_presence: null,
  };
}

function payload(overrides = {}) {
  const requirements = [
    requirement('GP-S1', 'SUPPORTED', { scope: 'Scope 1', requirement_class: 'REQUIRED' }),
    requirement('GP-S2-LB', 'SUPPORTED', {
      scope: 'Scope 2',
      scope2_method: 'LOCATION_BASED',
      requirement_class: 'REQUIRED',
    }),
    requirement('GP-S2-MB', 'MISSING_CAPABILITY', {
      scope: 'Scope 2',
      scope2_method: 'MARKET_BASED',
      requirement_class: 'REQUIRED',
      requirement_class_expression: 'NOT_SUPPORTED',
      supported: false,
    }),
  ];
  Object.entries(M1_IMAGE).forEach(([code, capability]) => {
    requirements.push(
      requirement(code, capability, {
        scope3_category: Number(code.slice(-2)),
        supported: capability !== 'MISSING_CAPABILITY' && capability !== 'FUTURE',
        requirement_class_expression:
          capability === 'MISSING_CAPABILITY'
            ? 'NOT_SUPPORTED'
            : capability === 'FUTURE'
              ? 'FUTURE'
              : 'CONDITIONAL',
      }),
    );
  });
  return {
    surface: 'CAPABILITY_TRUTH',
    framework: {
      code: 'GHG_PROTOCOL',
      name: 'GHG Protocol Corporate Standard',
      publisher: 'GHG Protocol / WRI & WBCSD',
      kind: 'accounting_foundation',
    },
    framework_version: {
      version_label: 'Corporate Accounting and Reporting Standard (2004 revised edition)',
      status: 'IN_FORCE',
      source_tier: 1,
      source_url: 'https://ghgprotocol.org/corporate-standard',
      authoritative_source_date: null,
    },
    capability_vocabulary: VOCABULARY,
    capability_glossary: VOCABULARY.map((value) => ({ value, explanation: EXPLANATION[value] })),
    requirements,
    scope3_capability_rollup: ROLLUP,
    scope3_rollup_basis:
      'Derived from the persisted governed catalogue rows. The split is shown in full and is never aggregated into a total, a coverage figure or a count of supported categories.',
    result_presence_note:
      'Capability and results are different facts. This projection states what the product supports; it carries no result for any organisation.',
    ...overrides,
  };
}

const domText = () => document.body.textContent;

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(cleanup);


async function renderCustomer() {
  api.getCapabilityCatalogue.mockResolvedValue(payload());
  const view = render(<CapabilitiesPage />);
  await screen.findByText(/What CarbonTally supports/i);
  return view;
}

async function renderInvestor() {
  api.getCapabilityCatalogue.mockResolvedValue(payload());
  const view = render(<InvestorCapabilityPage />);
  await screen.findByText(/CarbonTally product capabilities/i);
  return view;
}

// ===========================================================================
// §5 — the frontend owns no capability fact
// ===========================================================================
test('the surfaces hardcode no capability vocabulary and no category table', () => {
  const root = path.resolve(__dirname, '../../..');
  const files = [
    'src/v3/components/CapabilityTruthSurface.jsx',
    'src/v3/capabilities/CapabilitiesPage.jsx',
    'src/v3/capabilities/InvestorCapabilityPage.jsx',
  ];
  files.forEach((relative) => {
    const source = fs.readFileSync(path.join(root, relative), 'utf8');
    expect(source).not.toMatch(/GP-S3-CAT-/);
    expect(source).not.toMatch(/M1_IMAGE/);
  });
  const surface = fs.readFileSync(
    path.join(root, 'src/v3/components/CapabilityTruthSurface.jsx'),
    'utf8',
  );
  // The governed value rendered is the one the payload carried.
  expect(surface).toMatch(/carbontally_capability/);
  expect(surface).toMatch(/capability_vocabulary/);
});

// ===========================================================================
// AG-1 / AG-6 — the governed value is quoted verbatim on both surfaces
// ===========================================================================
test('ag_1/ag_6 both surfaces render the same governed value per requirement', async () => {
  await renderCustomer();
  const customerCell = document.querySelector('[data-requirement="GP-S3-CAT-02"] th + td + td');
  expect(customerCell.textContent).toContain('MISSING_CAPABILITY');
  cleanup();

  await renderInvestor();
  const investorCell = document.querySelector('[data-requirement="GP-S3-CAT-02"] th + td + td');
  expect(investorCell.textContent).toContain('MISSING_CAPABILITY');
});

test('every projected capability value is rendered', async () => {
  await renderCustomer();
  expect(domText()).toContain('SUPPORTED');
  expect(domText()).toContain('PARTIALLY_SUPPORTED');
  expect(domText()).toContain('FUTURE');
  expect(domText()).toContain('MISSING_CAPABILITY');
});

// ===========================================================================
// AG-3 — no Axis-A token is rendered
// ===========================================================================
test('ag_3 no Axis-A token is rendered on either surface', async () => {
  await renderCustomer();
  // Word-boundary: PARTIALLY_SUPPORTED is a governed value, PARTIAL is not.
  expect(domText()).not.toMatch(/\b(PARTIAL|DEFERRED|NOT_IMPLEMENTED)\b/);
  cleanup();
  await renderInvestor();
  expect(domText()).not.toMatch(/\b(PARTIAL|DEFERRED|NOT_IMPLEMENTED)\b/);
  expect(domText()).not.toMatch(/architecture_status/);
});

// ===========================================================================
// AG-4 — no placeholder, no zero, no fabricated figure
// ===========================================================================
test('ag_4 no placeholder is rendered', async () => {
  await renderCustomer();
  const text = domText().toLowerCase();
  ['n/a', 'not applicable', 'excluded', 'coming soon', 'tbc', 'tbd'].forEach((token) => {
    expect(text).not.toContain(token);
  });
});

test('ag_4 no emissions figure is rendered', async () => {
  await renderCustomer();
  expect(domText()).not.toMatch(/\d[\d,]*(\.\d+)?\s*(kg|t|tonnes?|tCO2e)\b/i);
});

test('ag_4 a requirement with no result renders an explicit absence statement', async () => {
  await renderCustomer();
  const row = document.querySelector('[data-requirement="GP-S3-CAT-05"]');
  expect(row.textContent).toContain('No result is stated here for any organisation.');
  expect(row.textContent).not.toContain('0 tCO2e');
});

// ===========================================================================
// AG-7 — the four-way rollup is shown, never a total
// ===========================================================================
test('ag_7 the four-way rollup is rendered with its counts', async () => {
  await renderCustomer();
  const rollup = document.querySelector('.ct-capability__rollup');
  expect(rollup.textContent).toContain('SUPPORTED');
  expect(rollup.textContent).toContain('4');
  expect(rollup.textContent).toContain('PARTIALLY_SUPPORTED');
  expect(rollup.textContent).toContain('6');
  expect(rollup.textContent).toContain('FUTURE');
  expect(rollup.textContent).toContain('3');
  expect(rollup.textContent).toContain('MISSING_CAPABILITY');
  expect(rollup.textContent).toContain('2');
});

test('ag_7 no total, coverage percentage or all-15 claim is rendered', async () => {
  await renderCustomer();
  const text = domText().toLowerCase();
  expect(text).not.toContain('15 categories supported');
  expect(text).not.toContain('all 15');
  expect(text).not.toMatch(/\b\d+\s*\/\s*15\b/);
  expect(text).not.toMatch(/\b\d+\s*%/);
  // The rollup element itself carries the split and no total.
  const rollup = document.querySelector('.ct-capability__rollup');
  expect(rollup.querySelectorAll('.ct-capability__rollup-item').length).toBe(4);
});

// ===========================================================================
// AG-8 — provenance, or an explicit unresolved marker
// ===========================================================================
test('ag_8 provenance and the unresolved marker are rendered', async () => {
  await renderCustomer();
  expect(domText()).toContain('GHG Protocol Corporate Value Chain (Scope 3) Standard');
  expect(domText()).toContain('Source tier 1');
  expect(domText()).toContain('Authoritative identifier unresolved');
});


// ===========================================================================
// AG-5 / CS-1 — the product/investor surface is tenant-free
// ===========================================================================
test('ag_5 the product surface opens no tenant query path', () => {
  const root = path.resolve(__dirname, '../../..');
  const investor = fs.readFileSync(
    path.join(root, 'src/v3/capabilities/InvestorCapabilityPage.jsx'),
    'utf8',
  );
  // It must not resolve an organisation, and must not accept or send one.
  expect(investor).not.toMatch(/resolveV3Organization/);
  expect(investor).not.toMatch(/organizationId|organization_id/);
  expect(investor).not.toMatch(/facility|supplier|report|snapshot/i);
  // The one request it makes carries no tenant parameter.
  expect(investor).toMatch(/getCapabilityCatalogue\(\)/);
});

test('ag_5 no tenant identifier is rendered on either surface', async () => {
  const tenantTokens = [
    /organization_id/i,
    /organisation_id/i,
    /tenant_id/i,
    /facility_id/i,
    /supplier_id/i,
    /aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/,
  ];
  await renderCustomer();
  tenantTokens.forEach((token) => expect(domText()).not.toMatch(token));
  cleanup();
  await renderInvestor();
  tenantTokens.forEach((token) => expect(domText()).not.toMatch(token));
});

test('ag_5 the product surface is visibly labelled as product-level', async () => {
  await renderInvestor();
  expect(domText()).toContain('Product-level capability');
  expect(domText()).toContain('contains no customer or organisation information');
});

// ===========================================================================
// §8 — capability ≠ result: the absence statement, never a zero
// ===========================================================================
test('the capability-is-not-a-result statement is rendered on both surfaces', async () => {
  await renderCustomer();
  expect(domText()).toContain('Capability is not a result');
  cleanup();
  await renderInvestor();
  expect(domText()).toContain('Capability is not a result');
});

test('the customer surface points to its own results, the product surface does not', async () => {
  await renderCustomer();
  expect(domText()).toContain('Your own calculated results live on your');
  cleanup();
  await renderInvestor();
  expect(domText()).not.toContain('Your own calculated results live on your');
});

// ===========================================================================
// Fail-safe rendering
// ===========================================================================
test('an unrecognised capability value is still rendered verbatim', async () => {
  const data = payload();
  data.requirements = data.requirements.map((item) =>
    item.requirement_code === 'GP-S3-CAT-07'
      ? { ...item, carbontally_capability: 'SOMETHING_ELSE' }
      : item,
  );
  api.getCapabilityCatalogue.mockResolvedValue(data);
  render(<CapabilitiesPage />);
  await screen.findByText(/What CarbonTally supports/i);
  // IV-4: say less, never something invented — the value is shown, not hidden.
  expect(domText()).toContain('SOMETHING_ELSE');
});

test('a failing load shows a bounded error with a retry, never a claim', async () => {
  api.getCapabilityCatalogue.mockRejectedValue(new Error('Unable to load the capability statement.'));
  render(<CapabilitiesPage />);
  await screen.findByText(/Capability statement unavailable/i);
  expect(domText()).not.toContain('SUPPORTED');
  cleanup();

  api.getCapabilityCatalogue.mockResolvedValue(payload());
  const retryView = render(<CapabilitiesPage />);
  await screen.findByText(/What CarbonTally supports/i);
  expect(retryView).toBeTruthy();
});

test('the error state retries through the same single request', async () => {
  api.getCapabilityCatalogue.mockRejectedValueOnce(new Error('temporary failure.'));
  render(<CapabilitiesPage />);
  await screen.findByText(/Capability statement unavailable/i);
  api.getCapabilityCatalogue.mockResolvedValue(payload());
  fireEvent.click(screen.getByRole('button', { name: /retry/i }));
  await waitFor(() => expect(api.getCapabilityCatalogue).toHaveBeenCalledTimes(2));
});

test('the glossary explains the governed vocabulary it renders', async () => {
  await renderCustomer();
  const glossary = document.querySelector('.ct-capability__glossary');
  expect(glossary.textContent).toContain('NOT_APPLICABLE_TO_PRODUCT');
  expect(glossary.textContent).toMatch(/governed capability vocabulary/i);
  expect(glossary.textContent).toContain(EXPLANATION.NOT_APPLICABLE_TO_PRODUCT);
});

