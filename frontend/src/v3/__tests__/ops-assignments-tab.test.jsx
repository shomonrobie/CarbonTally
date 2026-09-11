// frontend/src/v3/__tests__/ops-assignments-tab.test.jsx
// WS4D — Operations item-level processing assignment UI tests. Covers the 4C
// API consumption: assign unassigned item -> PE, reassign PE->PE and
// PE->Internal, canonical effective display (batch default / item assignment /
// effective), mixed-batch rows, target lists (active PEs only / internal staff
// only), server validation error reflection, and the internal "Open item"
// deep link for an internally assigned item in a PE-defaulted batch.
import React from 'react';
import { render, screen, within, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Repo convention — react-router-dom is mocked (CRA jest 27 cannot resolve the
// v7 subpath export). Link renders a plain anchor so href assertions work.
jest.mock('react-router-dom', () => ({
  Link: ({ to, children, ...rest }) => (
    <a href={typeof to === 'string' ? to : '/'} {...rest}>{children}</a>
  ),
}));

jest.mock('../api', () => ({
  getOperatorQueue: jest.fn(),
  getOpsBatchItems: jest.fn(),
  listOpsStaff: jest.fn(),
  listProcessingEntities: jest.fn(),
  getEntityExtractionBatches: jest.fn(),
  opsWorkInfo: jest.fn(),
  opsWorkAssignTarget: jest.fn(),
  opsWorkReassignTarget: jest.fn(),
  opsWorkClaim: jest.fn(),
  opsWorkRelease: jest.fn(),
  opsWorkComplete: jest.fn(),
}));

import OpsAssignmentsTab from '../ops/OpsAssignmentsTab';
import * as api from '../api';

const ALPHA = 'e-alpha';
const BETA = 'e-beta';
const OP = 'u-operator';
const ADMIN = 'u-admin';
const PE_STAFF = 'u-pe-staff';

const B_INT = { id: 'b-int', batch_name: 'Internal invoice batch', entity_id: null, assigned_to: null, status: 'open', organization_id: 'org-x' };
const B_ALPHA = { id: 'b-alpha', batch_name: 'Alpha default batch', entity_id: ALPHA, assigned_to: null, status: 'open', organization_id: 'org-x' };

const items = {
  A: { id: 'item-a', file_name: 'purchases-A.pdf', status: 'extracting' },
  B: { id: 'item-b', file_name: 'purchases-B.pdf', status: 'extracting' },
  D: { id: 'item-d', file_name: 'energy-D.csv', status: 'extracting' },
  C: { id: 'item-c', file_name: 'travel-C.csv', status: 'extracting' },
};

const row = (overrides) => ({
  id: 'w1', status: 'open', action: 'assign', assignee_kind: 'processing_entity',
  assigned_to: null, processing_entity_id: null, assigned_by: ADMIN,
  actor_domain: 'internal_staff', previous_assigned_to: null,
  previous_processing_entity_id: null, reason: null,
  created_at: '2026-09-04T08:00:00Z', updated_at: '2026-09-04T08:00:00Z',
  ...overrides,
});

const workInfo = (current, effective) => ({
  item_id: 'x', batch_id: B_ALPHA.id, batch_entity_id: ALPHA, item_status: 'extracting',
  current, history: current ? [current] : [], effective,
  processing_origin: current && current.assignee_kind === 'processing_entity' ? 'PROCESSING_ENTITY' : null,
  processing_entity_id: (current && current.processing_entity_id) || null,
});

const workMap = {
  'item-a': workInfo(row({ processing_entity_id: ALPHA }),
    { kind: 'processing_entity', assignee: ALPHA, source: 'item' }),
  'item-b': workInfo(
    row({ id: 'wb', processing_entity_id: BETA, previous_processing_entity_id: ALPHA, action: 'reassign' }),
    { kind: 'processing_entity', assignee: BETA, source: 'item' }),
  'item-d': workInfo(row({ assignee_kind: 'internal_staff', assigned_to: OP }),
    { kind: 'internal_staff', assignee: OP, source: 'item' }),
  'item-c': workInfo(null, { kind: 'processing_entity', assignee: ALPHA, source: 'batch' }),
};

const defaultSetup = () => {
  api.getOperatorQueue.mockResolvedValue({
    batches: [{ batch: B_INT, organization: { id: 'org-x', name: 'Org X' } }],
  });
  api.listOpsStaff.mockResolvedValue({
    staff: [
      { user_id: OP, first_name: 'Demo', last_name: 'Operator', email: 'op@ct', is_active: true, entity_id: null, role_name: 'operator' },
      { user_id: ADMIN, first_name: 'Ops', last_name: 'Admin', email: 'admin@ct', is_active: true, entity_id: null, role_name: 'staff_admin' },
      { user_id: PE_STAFF, first_name: 'PE', last_name: 'Worker', email: 'pe@ct', is_active: true, entity_id: ALPHA, role_name: 'pe_manager' },
    ],
  });
  api.listProcessingEntities.mockResolvedValue({
    entities: [
      { id: ALPHA, name: 'PE Alpha', status: 'active' },
      { id: BETA, name: 'PE Beta', status: 'active' },
      { id: 'e-retired', name: 'PE Retired', status: 'inactive' },
    ],
  });
  api.getEntityExtractionBatches.mockImplementation(async (entityId) => ({
    batches: entityId === ALPHA ? [B_ALPHA] : [],
  }));
  api.getOpsBatchItems.mockResolvedValue({ batch: B_ALPHA, items: [items.A, items.B, items.D, items.C] });
  api.opsWorkInfo.mockImplementation(async (itemId) => workMap[itemId]);
  api.opsWorkAssignTarget.mockResolvedValue({ changed: true });
  api.opsWorkReassignTarget.mockResolvedValue({ changed: true });
  api.opsWorkClaim.mockResolvedValue({ changed: true });
  api.opsWorkRelease.mockResolvedValue({ changed: true });
  api.opsWorkComplete.mockResolvedValue({ changed: true });
};

const renderTab = () => render(<OpsAssignmentsTab />);

const openAlphaBatch = async () => {
  const alphaRow = await screen.findByText('Alpha default batch');
  fireEvent.click(within(alphaRow.closest('tr')).getByRole('button', { name: /Open items/i }));
  await screen.findByText('Items — Alpha default batch');
  await waitFor(() => {
    expect(api.opsWorkInfo).toHaveBeenCalledWith('item-a');
    expect(api.opsWorkInfo).toHaveBeenCalledWith('item-c');
  });
};

describe('OpsAssignmentsTab (WS4D item-level assignment UI)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    defaultSetup();
  });

  test('directory lists internal batches and active-PE default batches', async () => {
    renderTab();
    expect(await screen.findByText('Internal invoice batch')).toBeInTheDocument();
    expect(await screen.findByText('Alpha default batch')).toBeInTheDocument();
    expect(await screen.findByText(/2 batch/)).toBeInTheDocument();
    const alphaDirRow = (await screen.findByText('Alpha default batch')).closest('tr');
    expect(within(alphaDirRow).getByText('PE Alpha')).toBeInTheDocument();
  });

  test('mixed batch shows a per-item effective processor (never a single batch party)', async () => {
    renderTab();
    await openAlphaBatch();
    const aRow = screen.getByText('purchases-A.pdf').closest('tr');
    expect(within(aRow).getByText(/Effective: PE Alpha/)).toBeInTheDocument();
    expect(within(aRow).getByText(/item assignment/)).toBeInTheDocument();
    const bRow = screen.getByText('purchases-B.pdf').closest('tr');
    expect(within(bRow).getByText(/Effective: PE Beta/)).toBeInTheDocument();
    expect(within(bRow).getByText(/Previous: PE Alpha/)).toBeInTheDocument();
    const dRow = screen.getByText('energy-D.csv').closest('tr');
    expect(within(dRow).getByText(/Effective: Demo Operator/)).toBeInTheDocument();
    const cRow = screen.getByText('travel-C.csv').closest('tr');
    expect(within(cRow).getByText(/Batch default: PE Alpha/)).toBeInTheDocument();
    expect(within(cRow).getByText(/Effective: PE Alpha/)).toBeInTheDocument();
    expect(within(cRow).getByText(/batch default/)).toBeInTheDocument();
  });

  test('assigns an unassigned item to a processing entity via the 4C assign endpoint', async () => {
    renderTab();
    await openAlphaBatch();
    const cRow = screen.getByText('travel-C.csv').closest('tr');
    fireEvent.change(within(cRow).getByLabelText(/travel-C\.csv to processing entity/), { target: { value: BETA } });
    fireEvent.click(within(cRow).getByRole('button', { name: /Assign to PE/ }));
    await waitFor(() => {
      expect(api.opsWorkAssignTarget).toHaveBeenCalledWith('item-c', { entity_id: BETA });
    });
    expect(await screen.findByText(/Item assigned to the processing entity/)).toBeInTheDocument();
  });

  test('reassigns PE Alpha -> PE Beta through the reassign endpoint', async () => {
    renderTab();
    await openAlphaBatch();
    const aRow = screen.getByText('purchases-A.pdf').closest('tr');
    fireEvent.change(within(aRow).getByLabelText(/purchases-A\.pdf to processing entity/), { target: { value: BETA } });
    fireEvent.click(within(aRow).getByRole('button', { name: /Reassign to PE/ }));
    await waitFor(() => {
      expect(api.opsWorkReassignTarget).toHaveBeenCalledWith('item-a', { entity_id: BETA });
    });
  });

  test('reassigns PE -> internal staff through the reassign endpoint', async () => {
    renderTab();
    await openAlphaBatch();
    const bRow = screen.getByText('purchases-B.pdf').closest('tr');
    fireEvent.change(within(bRow).getByLabelText(/purchases-B\.pdf to internal staff/), { target: { value: OP } });
    fireEvent.click(within(bRow).getByRole('button', { name: /Reassign to staff/ }));
    await waitFor(() => {
      expect(api.opsWorkReassignTarget).toHaveBeenCalledWith('item-b', { assigned_to: OP });
    });
  });

  test('internal target list never exposes Processing Entity users', async () => {
    renderTab();
    await openAlphaBatch();
    const cRow = screen.getByText('travel-C.csv').closest('tr');
    const staffSelect = within(cRow).getByLabelText(/travel-C\.csv to internal staff/);
    const labels = Array.from(staffSelect.querySelectorAll('option')).map((o) => o.textContent);
    expect(labels.some((l) => l.includes('Demo Operator'))).toBe(true);
    expect(labels.some((l) => l.includes('PE Worker'))).toBe(false);
  });

  test('processing entity target list only offers active entities', async () => {
    renderTab();
    await openAlphaBatch();
    const cRow = screen.getByText('travel-C.csv').closest('tr');
    const peSelect = within(cRow).getByLabelText(/travel-C\.csv to processing entity/);
    const values = Array.from(peSelect.querySelectorAll('option')).map((o) => o.value);
    expect(values).toEqual(expect.arrayContaining([ALPHA, BETA]));
    expect(values).not.toContain('e-retired');
  });

  test('reflects server validation errors instead of hiding them', async () => {
    api.opsWorkAssignTarget.mockRejectedValue(new Error('target processing entity is not active'));
    renderTab();
    await openAlphaBatch();
    const cRow = screen.getByText('travel-C.csv').closest('tr');
    fireEvent.change(within(cRow).getByLabelText(/travel-C\.csv to processing entity/), { target: { value: BETA } });
    fireEvent.click(within(cRow).getByRole('button', { name: /Assign to PE/ }));
    expect(await screen.findByText('target processing entity is not active')).toBeInTheDocument();
  });

  test('Release/Complete are not offered for items effectively assigned to a PE', async () => {
    renderTab();
    await openAlphaBatch();
    const aRow = screen.getByText('purchases-A.pdf').closest('tr');
    expect(within(aRow).getByRole('button', { name: /Release/ })).toBeDisabled();
    expect(within(aRow).getByRole('button', { name: /Complete/ })).toBeDisabled();
    const dRow = screen.getByText('energy-D.csv').closest('tr');
    expect(within(dRow).getByRole('button', { name: /Release/ })).not.toBeDisabled();
    expect(within(dRow).getByRole('button', { name: /Complete/ })).not.toBeDisabled();
  });

  test('internally assigned item in a PE-defaulted batch has an internal Open-item path', async () => {
    renderTab();
    await openAlphaBatch();
    const dRow = screen.getByText('energy-D.csv').closest('tr');
    const link = within(dRow).getByRole('link', { name: /Open item/ });
    expect(link).toHaveAttribute('href', '/ops/items/item-d?tab=assignments');
    expect(within(dRow).getByRole('button', { name: /Assign to me/ })).toBeInTheDocument();
  });
});
