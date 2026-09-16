// frontend/src/__tests__/onboarding-canonical.test.jsx
// P8-FIN-01a — the canonical onboarding experience is the backend-driven
// `/onboarding` route (OnboardingPage). Organisation-less authenticated users
// reach it through RoleRoute (server-authoritative /api/v3/me/context), and the
// legacy OnboardingWizard overlay is retired: not imported, not mounted, and
// unreachable from the app shell.
import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import RoleRoute from '../v3/components/RoleRoute';

// react-router-dom v7 re-exports from `react-router` which jest cannot resolve;
// the codebase's convention is to stub the router primitives in tests. The
// redirect target is asserted through the stubbed Navigate.
jest.mock('react-router-dom', () => {
  const ReactActual = require('react');
  return {
    Navigate: ({ to }) => ReactActual.createElement('div', { 'data-testid': 'redirect' }, to),
  };
});

jest.mock('../v3/api', () => ({ getMeContext: jest.fn() }));

const { getMeContext } = jest.requireMock('../v3/api');

const SRC_ROOT = path.join(__dirname, '..');
const APP_SOURCE = fs.readFileSync(path.join(SRC_ROOT, 'App.js'), 'utf8');

const isTestFile = (file) => file.includes(`${path.sep}__tests__${path.sep}`)
  || /\.test\.(js|jsx)$/.test(file);

function walkSourceFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return walkSourceFiles(full);
    if (!/\.(js|jsx)$/.test(entry.name)) return [];
    return isTestFile(full) ? [] : [full];
  });
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('P8-FIN-01a — canonical onboarding flow', () => {
  it('sends an organisation-less authenticated user to /onboarding', async () => {
    getMeContext.mockResolvedValue({
      actor_type: 'customer',
      organization: null,
      destination: '/onboarding',
    });

    render(<RoleRoute requireOrg><div>Customer workspace</div></RoleRoute>);

    expect(await screen.findByTestId('redirect')).toHaveTextContent('/onboarding');
    expect(screen.queryByText('Customer workspace')).not.toBeInTheDocument();
  });

  it('leaves an existing organisation member in their workspace', async () => {
    getMeContext.mockResolvedValue({
      actor_type: 'customer',
      organization: { id: 'org-1', name: 'Acme Ltd' },
      destination: '/home',
    });

    render(<RoleRoute requireOrg><div>Customer workspace</div></RoleRoute>);

    expect(await screen.findByText('Customer workspace')).toBeInTheDocument();
    expect(screen.queryByTestId('redirect')).not.toBeInTheDocument();
  });

  it('never mounts the retired legacy OnboardingWizard overlay', () => {
    expect(APP_SOURCE).not.toMatch(/<OnboardingWizard/);
    expect(APP_SOURCE).not.toMatch(new RegExp(`^\\s*import\\s+Onboarding${'Wizard'}`, 'm'));
  });

  it('has no remaining wizard state or wizard launch control in the app shell', () => {
    expect(APP_SOURCE).not.toMatch(/setShowOnboarding\s*\(/);
    expect(APP_SOURCE).not.toMatch(/\bshowOnboarding\s*&&/);
    expect(APP_SOURCE).not.toMatch(/setOnboardingChecked\s*\(/);
  });

  it('keeps the canonical /onboarding route backed by OnboardingPage', () => {
    expect(APP_SOURCE).toMatch(/path="\/onboarding"/);
    expect(APP_SOURCE).toMatch(/<OnboardingPage/);
  });

  it('is not imported anywhere in the application source (unreachable)', () => {
    const importPattern = new RegExp(`import\\s+Onboarding${'Wizard'}`);
    const referencing = walkSourceFiles(SRC_ROOT)
      .filter((file) => importPattern.test(fs.readFileSync(file, 'utf8')));

    expect(referencing).toEqual([]);
  });
});
