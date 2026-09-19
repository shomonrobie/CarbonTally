// frontend/src/__tests__/entity-routing-guards.test.jsx
// Workstream E (entity routing) — the two STAFF domains must not be interchangeable.
//
// The server is authoritative and already separates them:
//   /api/v3/me/context → actor_type 'staff'        (CarbonTally internal) → destination /ops
//                        actor_type 'entity_staff' (Processing Entity)    → destination /pe
//   api/pe_auth.py     → internal staff are DENIED on /api/v3/pe/*
//   api/operations_auth.py → entity staff are DENIED on the operations surfaces
// A single `requireStaff` guard on both route families admitted each domain into the other's
// shell, where every API call answers 403. These tests pin the split AND the redirect target
// (an existing user is returned to the workspace the server assigns them, never to the
// public site).
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

beforeEach(() => {
  jest.clearAllMocks();
});

describe('workstream E — entity/ops routing guards', () => {
  it('admits Processing Entity staff into the PE workspace', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'entity_staff', destination: '/pe' });

    render(<RoleRoute requireEntityStaff><div>PE workspace</div></RoleRoute>);

    expect(await screen.findByText('PE workspace')).toBeInTheDocument();
  });

  it('redirects internal CarbonTally staff away from the PE workspace to /ops', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'staff', destination: '/ops' });

    render(<RoleRoute requireEntityStaff><div>PE workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/ops');
    expect(screen.queryByText('PE workspace')).not.toBeInTheDocument();
  });

  it('admits internal CarbonTally staff into the operations console', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'staff', destination: '/ops' });

    render(<RoleRoute requireInternalStaff><div>Ops console</div></RoleRoute>);

    expect(await screen.findByText('Ops console')).toBeInTheDocument();
  });

  it('redirects Processing Entity staff away from the operations console to /pe', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'entity_staff', destination: '/pe' });

    render(<RoleRoute requireInternalStaff><div>Ops console</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/pe');
    expect(screen.queryByText('Ops console')).not.toBeInTheDocument();
  });

  it('redirects a customer to their own workspace rather than the public site', async () => {
    getMeContext.mockResolvedValue({
      actor_type: 'customer',
      organization: { id: 'org-1' },
      destination: '/home',
    });

    render(<RoleRoute requireEntityStaff><div>PE workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/home');
  });

  it('redirects a consultant to their portfolio', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'consultant', destination: '/consultant' });

    render(<RoleRoute requireInternalStaff><div>Ops console</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/consultant');
  });

  it('still honours an explicit fallback when one is provided', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'customer', organization: { id: 'o' }, destination: '/home' });

    render(<RoleRoute requireEntityStaff fallback="/pricing"><div>PE</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/pricing');
  });

  it('keeps an organisation-less authenticated user on the onboarding path', async () => {
    getMeContext.mockResolvedValue({ actor_type: 'customer', organization: null, destination: '/onboarding' });

    render(<RoleRoute requireInternalStaff><div>Ops console</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/onboarding');
  });
});

describe('workstream E — the App.js routing table matches the domain split', () => {
  const guardsFor = (prefix) => {
    const pattern = new RegExp(
      `<Route path="${prefix}[^"]*"[\\s\\S]{0,160}?<RoleRoute (\\w+)>`, 'g');
    return [...APP_SOURCE.matchAll(pattern)].map((m) => m[1]);
  };

  it('every /pe route requires Processing Entity staff', () => {
    const guards = guardsFor('/pe');
    expect(guards.length).toBeGreaterThanOrEqual(4);
    expect(new Set(guards)).toEqual(new Set(['requireEntityStaff']));
  });

  it('every /ops route requires internal CarbonTally staff', () => {
    const guards = guardsFor('/ops');
    expect(guards.length).toBeGreaterThanOrEqual(4);
    expect(new Set(guards)).toEqual(new Set(['requireInternalStaff']));
  });

  it('every /consultant route requires a consultant', () => {
    const guards = guardsFor('/consultant');
    expect(guards.length).toBeGreaterThanOrEqual(2);
    expect(new Set(guards)).toEqual(new Set(['requireConsultant']));
  });

  it('no route falls back to the coarse staff union guard', () => {
    expect(APP_SOURCE).not.toContain('requireStaff');
  });
});
