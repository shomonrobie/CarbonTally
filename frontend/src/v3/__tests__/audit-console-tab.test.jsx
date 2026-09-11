// frontend/src/v3/__tests__/audit-console-tab.test.jsx
// BL-4 — the admin audit console: honest total, server-side sort resetting to
// page 1, debounced free-text search, admin-only gate, and load errors.
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  getOpsAudit: jest.fn(),
}));

import AuditConsoleTab from '../ops/AuditConsoleTab';
import * as api from '../api';

const makeEntries = (n) => Array.from({ length: n }, (_, i) => ({
  id: `audit-${i}`,
  entity_type: 'manual_extraction_item',
  entity_id: `ent-${i}`,
  action: i % 2 === 0 ? 'item:created' : 'item:updated',
  actor: `user-${i % 4}`,
  occurred_at: '2025-01-01T00:00:00Z',
  reason: null,
  changed_fields: ['status'],
}));

beforeEach(() => {
  jest.clearAllMocks();
  api.getOpsAudit.mockResolvedValue({ entries: makeEntries(5), total: 123 });
});

describe('AuditConsoleTab (BL-4)', () => {
  test('renders entries with an honest total from the server', async () => {
    render(<AuditConsoleTab canManage />);
    expect(await screen.findByText(/Audit trail — 123 entries/)).toBeInTheDocument();
    expect(screen.getByText('user-1')).toBeInTheDocument();
    expect(screen.getAllByRole('row').length).toBeGreaterThan(1);
  });

  test('reserves the console for staff admin', () => {
    render(<AuditConsoleTab canManage={false} />);
    expect(screen.getByText(/Audit is admin-only/)).toBeInTheDocument();
    expect(api.getOpsAudit).not.toHaveBeenCalled();
  });

  test('server-side sort resets to page 1 and forwards sort/order', async () => {
    render(<AuditConsoleTab canManage />);
    await screen.findByText(/Audit trail — 123 entries/);

    fireEvent.click(screen.getByRole('button', { name: /actor/i }));
    await waitFor(() => {
      expect(api.getOpsAudit).toHaveBeenCalledWith(
        expect.objectContaining({ sort: 'actor', order: 'asc', offset: 0 }),
      );
    });
  });

  test('free-text search is debounced and forwarded', async () => {
    render(<AuditConsoleTab canManage />);
    await screen.findByText(/Audit trail — 123 entries/);

    fireEvent.change(screen.getByLabelText(/search/i), { target: { value: 'item:created' } });
    await waitFor(() => {
      expect(api.getOpsAudit).toHaveBeenCalledWith(
        expect.objectContaining({ q: 'item:created', offset: 0 }),
      );
    }, { timeout: 2500 });
  });

  test('load failures surface an alert', async () => {
    api.getOpsAudit.mockRejectedValue(new Error('audit unavailable'));
    render(<AuditConsoleTab canManage />);
    expect(await screen.findByText(/audit unavailable/i)).toBeInTheDocument();
  });
});
