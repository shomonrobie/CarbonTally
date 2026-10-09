// frontend/src/v3/__tests__/consultant-team-capabilities.test.jsx
// CT-CONSULTANT-MODEL-IMPLEMENTATION-03 (F-1/F-2 wiring, P1/P5).
//
// The CT02 backend capability endpoint existed with no consumer. These tests pin
// the UI wiring without claiming to be the security boundary: the server remains
// authoritative (self-escalation 422, cross-firm 404, unknown field 422 are all
// asserted BACKEND-side in test_ct_consultant_model_03.py). Here we assert the
// UI (a) surfaces the full capability set, (b) offers grant/revoke only to a
// can_manage_team caller, (c) never offers self-editing, and (d) writes exactly
// the draft the server will validate.
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

const USER_ID = 'u-cons';
const COLLEAGUE_ID = 'u-second';

jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getUser: jest.fn() } },
}));

jest.mock('../api', () => {
  const actual = jest.requireActual('../api');
  return {
    ...actual,
    getConsultantTeam: jest.fn(),
    getConsultantTasks: jest.fn(),
    addConsultantTeamMember: jest.fn(),
    createConsultantTask: jest.fn(),
    listConsultantClients: jest.fn(),
    updateConsultantTeamMemberCapabilities: jest.fn(),
  };
});

import ConsultantTeamTab from '../consultant/ConsultantTeamTab';
import * as api from '../api';
import { supabase } from '../../supabaseClient';

function members(ownerManageTeam) {
  return [
    {
      id: `fm-${USER_ID}`,
      user_id: USER_ID,
      role: 'owner',
      email: 'owner@firm.test',
      is_active: true,
      can_view_client: true,
      can_approve: false,
      can_manage_clients: true,
      can_manage_team: ownerManageTeam,
      can_upload_documents: false,
      can_generate_reports: false,
      can_extract: false,
      can_map: false,
      can_validate: false,
      can_calculate: false,
      can_confirm_automation: false,
      can_submit: false,
    },
    {
      id: `fm-${COLLEAGUE_ID}`,
      user_id: COLLEAGUE_ID,
      role: 'consultant',
      email: 'second@firm.test',
      is_active: true,
      can_view_client: true,
      can_approve: false,
      can_manage_clients: false,
      can_manage_team: false,
      can_upload_documents: false,
      can_generate_reports: false,
      can_extract: false,
      can_map: true,
      can_validate: false,
      can_calculate: false,
      can_confirm_automation: false,
      can_submit: false,
    },
  ];
}

beforeEach(() => {
  jest.clearAllMocks();
  supabase.auth.getUser.mockResolvedValue({ data: { user: { id: USER_ID } } });
  api.getConsultantTasks.mockResolvedValue({ tasks: [] });
  api.listConsultantClients.mockResolvedValue({
    clients: [
      { id: 'client-1', client_name: 'Quayside Energy', status: 'active' },
      { id: 'client-2', client_name: 'Granite Distribution', status: 'active' },
    ],
  });
});

const rosterLoaded = () =>
  waitFor(() =>
    expect(screen.getAllByText('second@firm.test').length).toBeGreaterThan(0)
  );

it('surfaces the full capability set and offers grant/revoke to a firm admin', async () => {
  api.getConsultantTeam.mockResolvedValue({ members: members(true) });
  render(<ConsultantTeamTab />);

  await rosterLoaded();
  // The two CT02 capabilities are surfaced in the roster.
  expect(screen.getAllByText(/view client/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/map/).length).toBeGreaterThan(0);
  // The colleague can be edited; the caller's OWN row cannot (no self-escalation).
  const editButtons = screen.getAllByText('Edit capabilities');
  expect(editButtons).toHaveLength(1);
  fireEvent.click(editButtons[0]);
  expect(await screen.findByText('Approve (final)')).toBeInTheDocument();
});

it('does not offer capability administration to a non-manage_team caller', async () => {
  api.getConsultantTeam.mockResolvedValue({ members: members(false) });
  render(<ConsultantTeamTab />);
  await rosterLoaded();
  expect(screen.queryByText('Edit capabilities')).toBeNull();
});

it('writes exactly the draft the server will validate', async () => {
  api.getConsultantTeam.mockResolvedValue({ members: members(true) });
  api.updateConsultantTeamMemberCapabilities.mockResolvedValue({
    member: { id: `fm-${COLLEAGUE_ID}`, can_approve: true },
  });
  render(<ConsultantTeamTab />);
  await rosterLoaded();

  fireEvent.click(screen.getAllByText('Edit capabilities')[0]);
  const approve = await screen.findByLabelText('Approve (final)');
  fireEvent.click(approve);
  fireEvent.click(screen.getByText('Save capabilities'));

  await waitFor(() =>
    expect(api.updateConsultantTeamMemberCapabilities).toHaveBeenCalledWith(
      `fm-${COLLEAGUE_ID}`,
      expect.objectContaining({ can_approve: true, can_map: true })
    )
  );
});

// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A — human-UX cleanup of the Team tab.

it('adds a member by EMAIL, never by an internal user id (UX-11/AC-14)', async () => {
  api.getConsultantTeam.mockResolvedValue({ members: members(true) });
  api.addConsultantTeamMember.mockResolvedValue({ id: 'fm-new', role: 'consultant' });
  render(<ConsultantTeamTab />);
  await rosterLoaded();

  // No raw "User id" field exists any more.
  expect(screen.queryByLabelText(/user id/i)).toBeNull();
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'Jane@Firm.test' } });
  fireEvent.click(screen.getByRole('button', { name: /add team member/i }));

  await waitFor(() =>
    expect(api.addConsultantTeamMember).toHaveBeenCalledWith({
      email: 'jane@firm.test',
      role: 'consultant',
    })
  );
});

it('offers the REAL backend role vocabulary, not an invented label (UX-13/AC-16)', async () => {
  api.getConsultantTeam.mockResolvedValue({ members: members(true) });
  render(<ConsultantTeamTab />);
  await rosterLoaded();

  const roleSelect = screen.getByLabelText('Role');
  const values = Array.from(roleSelect.querySelectorAll('option')).map((o) => o.value);
  expect(values).toEqual(['consultant', 'manager', 'viewer', 'owner']);
  // The previous UI offered a value the API rejects (422).
  expect(values).not.toContain('consultant team member');
});

it('offers a human-readable, authorized client selector for firm tasks (UX-18/AC-18)', async () => {
  api.getConsultantTeam.mockResolvedValue({ members: members(true) });
  render(<ConsultantTeamTab />);
  await rosterLoaded();

  const clientSelect = await screen.findByLabelText('Client (optional)');
  const optionValues = Array.from(clientSelect.querySelectorAll('option')).map((o) => o.value);
  const optionLabels = Array.from(clientSelect.querySelectorAll('option')).map((o) => o.textContent);
  expect(optionLabels).toContain('Quayside Energy');
  expect(optionLabels).toContain('— No specific client —');
  // The user never sees or types a raw client id.
  expect(optionLabels).not.toContain('client-1');
  // The empty option keeps a firm-wide task possible.
  expect(optionValues).toContain('');
});
