// frontend/src/v3/__tests__/pe-work-items-page.test.jsx
// WS4D — the dedicated PE application must never receive CarbonTally
// Operations assignment controls, and must render only the work the server
// reports as effectively assigned to this entity (server-filtered contract).
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Repo convention — react-router-dom is mocked (CRA jest 27 cannot resolve the
// v7 subpath export); Link renders a plain anchor.
jest.mock('react-router-dom', () => ({
  Link: ({ to, children, ...rest }) => (
    <a href={typeof to === 'string' ? to : '/'} {...rest}>{children}</a>
  ),
}));

jest.mock('../api', () => ({
  getPeMe: jest.fn(),
  getPeWork: jest.fn(),
  getPeBatchItems: jest.fn(),
  peWorkInfo: jest.fn(),
  peWorkClaim: jest.fn(),
  peWorkRelease: jest.fn(),
  peWorkComplete: jest.fn(),
}));

import PeWorkItemsPage from '../pe/PeWorkItemsPage';
import * as api from '../api';

const ALPHA = 'e-alpha';
const BETA = 'e-beta';

const batchAlpha = { id: 'b-alpha', batch_name: 'Alpha default batch', entity_id: ALPHA };

const itemD1 = { id: 'item-d1', file_name: 'assigned-to-alpha.pdf', status: 'extracting', batch_name: 'Alpha default batch', entity_id: ALPHA };
const itemD2 = { id: 'item-d2', file_name: 'second-alpha.xlsx', status: 'mapping', batch_name: 'Alpha default batch', entity_id: ALPHA };

const setup = () => {
  api.getPeMe.mockResolvedValue({
    entity: { id: ALPHA, name: 'PE Alpha' },
    profile: { role_name: 'pe_manager' },
  });
  api.getPeWork.mockResolvedValue({ batches: [batchAlpha] });
  // The /pe surface is server-filtered to items effectively assigned to Alpha:
  // a Beta item would never be present in this list.
  api.getPeBatchItems.mockResolvedValue({ batch: batchAlpha, items: [itemD1, itemD2] });
  api.peWorkInfo.mockResolvedValue({
    item_id: 'item-d1',
    batch_id: batchAlpha.id,
    batch_entity_id: ALPHA,
    current: {
      id: 'w1', status: 'open', action: 'claim', assignee_kind: 'processing_entity',
      assigned_to: null, processing_entity_id: ALPHA, assigned_by: 'u-admin',
      actor_domain: 'internal_staff', previous_assigned_to: null,
      previous_processing_entity_id: null, reason: null,
      created_at: '2026-09-04T08:00:00Z',
    },
    history: [{ id: 'w1', action: 'claim', actor_domain: 'internal_staff', created_at: '2026-09-04T08:00:00Z' }],
    effective: { kind: 'processing_entity', assignee: ALPHA, source: 'item' },
    processing_origin: 'PROCESSING_ENTITY', processing_entity_id: ALPHA,
  });
  api.peWorkClaim.mockResolvedValue({ changed: true });
  api.peWorkRelease.mockResolvedValue({ changed: true });
  api.peWorkComplete.mockResolvedValue({ changed: true });
};

describe('PeWorkItemsPage (WS4D PE boundary)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setup();
  });

  test('renders only the effectively assigned items the server returned', async () => {
    render(<PeWorkItemsPage />);
    expect(await screen.findByText('assigned-to-alpha.pdf')).toBeInTheDocument();
    expect(screen.getByText('second-alpha.xlsx')).toBeInTheDocument();
    expect(screen.getByText(/2 items for your Processing Entity/)).toBeInTheDocument();
  });

  test('never offers CarbonTally Operations assignment controls to PE staff', async () => {
    render(<PeWorkItemsPage />);
    await screen.findByText('assigned-to-alpha.pdf');
    // No target selectors and no Ops assign/reassign/claim-to-self buttons.
    expect(screen.queryByRole('combobox')).toBeNull();
    expect(screen.queryByRole('button', { name: /Assign to me/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Reassign/i })).toBeNull();
    // PE-only D38 controls remain (Claim / Release / Complete).
    expect(screen.getAllByRole('button', { name: /Claim/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /Release/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /Complete/i }).length).toBeGreaterThan(0);
  });

  test('reads assignment state from the PE work endpoint for display', async () => {
    render(<PeWorkItemsPage />);
    await screen.findByText('assigned-to-alpha.pdf');
    await waitFor(() => {
      expect(api.peWorkInfo).toHaveBeenCalledWith('item-d1');
    });
    await waitFor(() => {
      expect(screen.getAllByText(/Claimed \(this entity\)/).length).toBeGreaterThan(0);
    });
  });
});
