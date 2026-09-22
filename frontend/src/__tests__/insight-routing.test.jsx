// frontend/src/__tests__/insight-routing.test.jsx
// I6 — the Insight workspace is reachable only through the authenticated
// customer workspace (PO I6-1/I6-2), never through the public surface.
//
// The backend remains the authoritative security boundary (AGENTS.md §44): these
// tests pin the routing/guard wiring and the navigation entry, not access
// control. RoleRoute is UX navigation only and is exercised against the mocked
// server-authoritative /api/v3/me/context answer.
import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import RoleRoute from '../v3/components/RoleRoute';

jest.mock('react-router-dom', () => {
  const ReactActual = require('react');
  return {
    Navigate: ({ to }) => ReactActual.createElement('div', { 'data-testid': 'redirect' }, to),
  };
});

jest.mock('../v3/api', () => ({ getMeContext: jest.fn() }));

const { getMeContext } = jest.requireMock('../v3/api');
const APP_SOURCE = fs.readFileSync(path.join(__dirname, '..', 'App.js'), 'utf8');
const LAYOUT_SOURCE = fs.readFileSync(
  path.join(__dirname, '..', 'v3', 'components', 'V3Layout.jsx'),
  'utf8',
);

beforeEach(() => {
  jest.clearAllMocks();
});

describe('I6 — the /insight route is an authenticated customer-workspace route', () => {
  const routeWiring = () => {
    const match = APP_SOURCE.match(/<Route path="\/insight"[\s\S]{0,400}?\} \/>/);
    expect(match).not.toBeNull();
    return match[0];
  };

  test('the route is wired to InsightPage inside ProtectedRoute + the org guard + the v3 shell', () => {
    const wiring = routeWiring();
    expect(wiring).toContain('<ProtectedRoute>');
    expect(wiring).toContain('<RoleRoute requireOrg>');
    expect(wiring).toContain('<V3Layout>');
    expect(wiring).toContain('<InsightPage />');
  });

  test('the route does not fall back to the coarse staff union guard', () => {
    expect(routeWiring()).not.toContain('requireStaff');
  });

  test('Insight is not part of the public surface and never renders the public assistant', () => {
    const prefixes = APP_SOURCE.match(/const PUBLIC_ROUTE_PREFIXES = \[[\s\S]*?\];/)[0];
    expect(prefixes).not.toContain('insight');
    // The public assistant is mounted only for those prefixes.
    expect(APP_SOURCE).toContain('if (!isPublic) return null;');
  });
});

describe('I6 — the route guard behaves like the rest of the customer workspace', () => {
  test('an organisation member is admitted', async () => {
    getMeContext.mockResolvedValue({
      actor_type: 'customer',
      organization: { id: 'org-1' },
      destination: '/home',
    });

    render(<RoleRoute requireOrg><div>Insight workspace</div></RoleRoute>);

    expect(await screen.findByText('Insight workspace')).toBeInTheDocument();
  });

  test('a consultant is returned to their portfolio, not into Insight', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'consultant', destination: '/consultant' });

    render(<RoleRoute requireOrg><div>Insight workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/consultant');
    expect(screen.queryByText('Insight workspace')).not.toBeInTheDocument();
  });

  test('Processing Entity staff are returned to the PE application', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'entity_staff', destination: '/pe' });

    render(<RoleRoute requireOrg><div>Insight workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/pe');
  });

  test('internal CarbonTally staff are returned to the operations console', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'staff', destination: '/ops' });

    render(<RoleRoute requireOrg><div>Insight workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/ops');
  });

  test('an authenticated user with no organisation is sent to onboarding', async () => {
    getMeContext.mockResolvedValue({
      actor_type: 'customer',
      organization: null,
      destination: '/onboarding',
    });

    render(<RoleRoute requireOrg><div>Insight workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/onboarding');
  });

  test('a failed role resolution fails closed with an error, never a silent allow', async () => {
    getMeContext.mockRejectedValue(new Error('boom'));

    render(<RoleRoute requireOrg><div>Insight workspace</div></RoleRoute>);

    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn't verify your access/i);
    expect(screen.queryByText('Insight workspace')).not.toBeInTheDocument();
  });
});

describe('I6 — navigation entry', () => {
  test('Insight is offered in the customer navigation model', () => {
    expect(LAYOUT_SOURCE).toMatch(/\{ to: '\/insight', label: 'Insight'/);
    // It is inside the customer link set, so it is neither a staff nor a
    // consultant entry point (PO I6-1).
    const customerLinks = LAYOUT_SOURCE.match(/const CUSTOMER_LINKS = \[[\s\S]*?\];/)[0];
    expect(customerLinks).toContain("to: '/insight'");
  });
});
