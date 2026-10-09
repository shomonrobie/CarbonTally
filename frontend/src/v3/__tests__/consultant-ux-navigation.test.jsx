// frontend/src/v3/__tests__/consultant-ux-navigation.test.jsx
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-02/UX-04/UX-08/UX-09/UX-13).
//
// Pins the navigation/context contract introduced by this remediation:
//   * actor/subject relationship labels come from REAL consultant_clients fields
//     (never the word "Client" as an identity — UX-02);
//   * an OFF client portal does NOT stop the consultant operating (UX-08);
//   * a retained (ended) relationship is explained, not editable in the UI (UX-09);
//   * Manual Processing adapts to the plane: inside the client plane the CTA stays
//     in the consultant FIRM commercial context instead of the org-only /billing
//     route that bounced the consultant to /consultant (UX-13/AC-12/AC-13).
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';

jest.mock('../api', () => ({
  resolveV3Organization: jest.fn(),
  getMyManualProcessing: jest.fn(),
}));

import ManualProcessingPage from '../customer/ManualProcessingPage';
import {
  ConsultantClientProvider,
  clientPortalLabel,
  clientPortalNote,
  relationshipLabel,
} from '../consultant/ConsultantClientContext';
import * as api from '../api';

describe('consultant relationship / client-portal labels (UX-02/UX-08/UX-09)', () => {
  test('an active managed client reads as consultant-managed, not as "Client"', () => {
    const client = { status: 'active', client_access_profile: 'managed', retained_read_only: false };
    expect(relationshipLabel(client)).toBe('Consultant-managed · Active');
    expect(clientPortalLabel(client)).toBe('Client portal: Managed');
    expect(clientPortalNote(client)).toBe('');
  });

  test('an OFF client portal does not imply the consultant cannot operate', () => {
    const client = { status: 'active', client_access_profile: 'off' };
    expect(clientPortalLabel(client)).toBe('Client portal: Off');
    expect(clientPortalNote(client)).toMatch(/can still operate/i);
  });

  test('a retained (ended) relationship is explained, never editable-looking', () => {
    const client = { status: 'ended', retained_read_only: true };
    expect(relationshipLabel(client)).toBe('Retained · Read-only');
    expect(clientPortalNote(client)).toMatch(/retention policy/i);
  });

  test('a suspended relationship is stated', () => {
    expect(relationshipLabel({ status: 'suspended' })).toBe('Consultant-managed · Suspended');
  });
});

describe('Manual Processing CTA stays in the correct commercial context (UX-13)', () => {
  const NOT_ENTITLED = {
    effective_entitled: false,
    direct_entitled: false,
    sponsored_entitled: false,
    operational_status: 'not_configured',
    coverage_sources: [],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    api.resolveV3Organization.mockResolvedValue({ id: 'org-1', name: 'Acme Client' });
    api.getMyManualProcessing.mockResolvedValue(NOT_ENTITLED);
  });

  test('a DIRECT customer sees the customer plans destination', async () => {
    render(
      <MemoryRouter>
        <ManualProcessingPage />
      </MemoryRouter>,
    );
    const link = await screen.findByRole('link', { name: /view available plans/i });
    expect(link).toHaveAttribute('href', '/billing');
  });

  test('inside the client plane the CTA stays in the consultant FIRM context', async () => {
    render(
      <MemoryRouter>
        <ConsultantClientProvider value={{ active: true, clientId: 'client-1' }}>
          <ManualProcessingPage />
        </ConsultantClientProvider>
      </MemoryRouter>,
    );
    const link = await screen.findByRole('link', { name: /view firm coverage/i });
    expect(link).toHaveAttribute('href', '/consultant?view=coverage');
    // The client's own billing route is never offered from the consultant plane.
    expect(screen.queryByRole('link', { name: /view available plans/i })).not.toBeInTheDocument();
  });
});
