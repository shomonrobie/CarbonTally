// frontend/src/__tests__/accept-invitation.test.jsx
// CT-CONSULTANT-CLIENT-IDENTITY-04 (PD-1A) — the invitee's acceptance journey.
//
// The page must: read the single-use token from the link, require the invitee
// to authenticate with the INVITED email (existing Supabase Auth — no second
// auth system, no password stored by CarbonTally), exchange the token through
// the backend, and surface expired/used/invalid outcomes as SAFE errors.
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AcceptInvitation from '../AcceptInvitation';
import { supabase } from '../supabaseClient';
import { acceptInvitation, goToWorkspace } from '../v3/api';

// jest.mock() calls are hoisted above the imports by babel-jest, so the module
// graph under test still receives these doubles.
var mockAuthStateCallback;

jest.mock('../supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      onAuthStateChange: jest.fn(),
      signInWithPassword: jest.fn(),
      signUp: jest.fn(),
      signInWithOAuth: jest.fn(),
    },
  },
}));

jest.mock('../v3/api', () => ({
  acceptInvitation: jest.fn(),
  goToWorkspace: jest.fn(),
}));

const renderAt = (url) =>
  render(
    <MemoryRouter initialEntries={[url]}>
      <AcceptInvitation />
    </MemoryRouter>
  );

const statusError = (status) => Object.assign(new Error('request failed'), { status });

beforeEach(() => {
  jest.clearAllMocks();
  mockAuthStateCallback = null;
  sessionStorage.clear();
  supabase.auth.getSession.mockResolvedValue({ data: { session: null } });
  // The component subscribes to auth changes; capture the callback so a test
  // can deliver the SIGNED_IN event the real client would emit.
  supabase.auth.onAuthStateChange.mockImplementation((cb) => {
    mockAuthStateCallback = cb;
    return { data: { subscription: { unsubscribe: jest.fn() } } };
  });
  supabase.auth.signInWithPassword.mockResolvedValue({ error: null });
  supabase.auth.signUp.mockResolvedValue({ data: { session: null }, error: null });
  supabase.auth.signInWithOAuth.mockResolvedValue({});
  acceptInvitation.mockResolvedValue({
    status: 'accepted',
    organization_id: 'org-a',
    role: 'member',
  });
  goToWorkspace.mockResolvedValue(undefined);
});

test('a link without a token is reported safely', async () => {
  renderAt('/accept-invitation');
  expect(await screen.findByText(/link is incomplete/i)).toBeInTheDocument();
  expect(acceptInvitation).not.toHaveBeenCalled();
});

test('an unauthenticated invitee is offered sign-in / sign-up with the invited email', async () => {
  renderAt('/accept-invitation?token=tok-123');
  expect(await screen.findByText(/you'?ve been invited/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
  expect(acceptInvitation).not.toHaveBeenCalled();
});

test('signing in transitions to acceptance and lands on the workspace', async () => {
  renderAt('/accept-invitation?token=tok-123');
  await screen.findByText(/you'?ve been invited/i);

  fireEvent.change(screen.getByLabelText(/email/i), {
    target: { value: 'invitee@example.test' },
  });
  fireEvent.change(screen.getByLabelText(/password/i), {
    target: { value: 'sup3rsecret' },
  });
  fireEvent.click(screen.getByRole('button', { name: /sign in & accept/i }));

  await waitFor(() =>
    expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: 'invitee@example.test',
      password: 'sup3rsecret',
    })
  );

  // The session arrives (onAuthStateChange) → the token is exchanged.
  await act(async () => {
    mockAuthStateCallback('SIGNED_IN', { user: { email: 'invitee@example.test' } });
  });
  await waitFor(() => expect(acceptInvitation).toHaveBeenCalledWith('tok-123'));
  await waitFor(() =>
    expect(goToWorkspace).toHaveBeenCalledWith(expect.any(Function))
  );
});

test('an existing session auto-accepts without prompting', async () => {
  supabase.auth.getSession.mockResolvedValue({ data: { session: { user: {} } } });
  renderAt('/accept-invitation?token=tok-999');
  await waitFor(() => expect(acceptInvitation).toHaveBeenCalledWith('tok-999'));
  expect(goToWorkspace).toHaveBeenCalled();
});

test('an expired invitation shows a safe error and does not redirect', async () => {
  supabase.auth.getSession.mockResolvedValue({ data: { session: { user: {} } } });
  acceptInvitation.mockRejectedValue(statusError(410));
  renderAt('/accept-invitation?token=tok-expired');
  expect(await screen.findByText(/has expired/i)).toBeInTheDocument();
  expect(goToWorkspace).not.toHaveBeenCalled();
});

test('a reused invitation shows a safe error and does not redirect', async () => {
  supabase.auth.getSession.mockResolvedValue({ data: { session: { user: {} } } });
  acceptInvitation.mockRejectedValue(statusError(409));
  renderAt('/accept-invitation?token=tok-used');
  expect(await screen.findByText(/already been used/i)).toBeInTheDocument();
  expect(goToWorkspace).not.toHaveBeenCalled();
});
