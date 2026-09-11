// frontend/src/v3/__tests__/operations-page-assignment-gating.test.jsx
// WS4D — the Operations Assignments surface is an internal-CarbonTally surface:
// entity (PE) profiles are redirected to the dedicated PE application before
// any Operations tab (including Assignments) can render.
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => {
  const params = new URLSearchParams('tab=assignments');
  return {
    Navigate: ({ to }) => <div data-testid="navigate-to">{String(to)}</div>,
    useSearchParams: () => [params, jest.fn()],
  };
});

jest.mock('../api', () => ({
  getOpsMe: jest.fn(),
}));

jest.mock('../ops/OpsDashboard', () => () => <div>Dashboard stub</div>);
jest.mock('../ops/OperatorQueue', () => () => <div>Data entry stub</div>);
jest.mock('../ops/ProcessingEntitiesTab', () => () => <div>Entities stub</div>);
jest.mock('../ops/ReviewQueue', () => () => <div>Review stub</div>);
jest.mock('../ops/CtQcTab', () => () => <div>CT QC stub</div>);
jest.mock('../ops/QcQueue', () => () => <div>QC stub</div>);
jest.mock('../ops/SlaTab', () => () => <div>SLA stub</div>);
jest.mock('../ops/StaffRoster', () => () => <div>Staff stub</div>);
jest.mock('../ops/StaffRolesTab', () => () => <div>Roles stub</div>);
jest.mock('../ops/CommercialTab', () => () => <div>Commercial stub</div>);
jest.mock('../ops/SettingsTab', () => () => <div>Settings stub</div>);
jest.mock('../ops/IssuesTriageTab', () => () => <div>Issues stub</div>);
jest.mock('../ops/AuditConsoleTab', () => () => <div>Audit stub</div>);
jest.mock('../ops/OpsMessagingTab', () => () => <div>Messaging stub</div>);
jest.mock('../ops/OpsPeMessagingTab', () => () => <div>PE messages stub</div>);
jest.mock('../ops/OpsAssignmentsTab', () => () => <div>Assignment tab stub</div>);

import OperationsPage from '../ops/OperationsPage';
import * as api from '../api';

const internalOperator = {
  profile: { entity_id: null, role_name: 'operator', first_name: 'Demo', last_name: 'Operator' },
  permissions: { can_process: true, can_view_all: true, can_manage_staff: false, can_manage_billing: false },
};

const peProfile = {
  profile: { entity_id: 'e-alpha', role_name: 'pe_manager', first_name: 'PE', last_name: 'Admin' },
  permissions: {},
};

describe('OperationsPage assignment-surface gating (WS4D)', () => {
  beforeEach(() => jest.clearAllMocks());

  test('internal staff with can_process receive the Assignments tab', async () => {
    api.getOpsMe.mockResolvedValue(internalOperator);
    render(<OperationsPage />);
    expect(await screen.findByText(/Internal Operations/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Assignments/ })).toBeInTheDocument();
    // requestTab=assignments restores the assignment surface directly.
    expect(await screen.findByText('Assignment tab stub')).toBeInTheDocument();
    expect(screen.queryByTestId('navigate-to')).not.toBeInTheDocument();
  });

  test('PE staff are redirected to /pe and never see Operations assignment controls', async () => {
    api.getOpsMe.mockResolvedValue(peProfile);
    render(<OperationsPage />);
    await waitFor(() => {
      expect(api.getOpsMe).toHaveBeenCalled();
    });
    // The PE branch returns <Navigate to="/pe"> — no Operations chrome renders.
    expect(await screen.findByTestId('navigate-to')).toHaveTextContent('/pe');
    expect(screen.queryByText(/Internal Operations/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Assignments/ })).not.toBeInTheDocument();
    expect(screen.queryByText('Assignment tab stub')).not.toBeInTheDocument();
  });
});
