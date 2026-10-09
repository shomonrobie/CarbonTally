// frontend/src/v3/consultant/ClientAccessTab.jsx
// CT-CONSULTANT-CLIENT-ACCESS-UX-01 — the CONSULTANT-PLANE "Client Access" tab.
//
// Replaces the wrong path: a consultant operating a managed client previously saw
// the Organisation-admin "Members & Invitations" surface, which calls the
// ORGANISATION-scoped endpoints (GET /organizations/{id}/members = org member,
// POST /organizations/{id}/invitations = org admin). A consultant is NOT an
// organisation member (AGENTS.md §29), so those calls returned 403 and the UI
// reported "You don't have permission to access this area."
//
// This component wires the ALREADY-EXISTING, server-gated CT-04 consultant
// endpoints (CoStrict F3 closure) so an authorised consultant can invite a client
// BY EMAIL, review pending invitations, and manage client users — without ever
// seeing a raw user id, an invitation token or an accept link.
//
// It grants nothing: every call is re-authorised server-side against the caller's
// ACTIVE consultant-client grant plus the manage_clients capability (PD-1A/PD-2A,
// D15). The client id is presentation context only, never an authorisation.
import React, { useCallback, useEffect, useState } from 'react';
import {
  createClientInvitation,
  listClientInvitations,
  listClientUsers,
  revokeClientInvitation,
  updateClientUser,
} from '../api';

// The four client roles are the REAL organization_members vocabulary (PD-2A —
// owner/admin/member/viewer). The human-facing labels/descriptions are
// presentation only (§7); no second role system is introduced.
const CLIENT_ROLES = [
  {
    id: 'owner',
    label: 'Client Owner',
    description: 'Full control of the client organisation and its users',
  },
  {
    id: 'admin',
    label: 'Client Admin',
    description: 'Manage client users and organisation settings',
  },
  {
    id: 'member',
    label: 'Client Member',
    description: 'Contribute data and view reports',
  },
  {
    id: 'viewer',
    label: 'Client Viewer',
    description: 'Read-only access',
  },
];

const ROLE_LABEL = Object.fromEntries(CLIENT_ROLES.map((r) => [r.id, r.label]));
const roleLabel = (role) => ROLE_LABEL[role] || role || '—';

// Derived invitation state → badge class (pending/active/inactive families already
// styled by admin.css).
const STATE_BADGE = {
  pending: 'pending',
  accepted: 'active',
  revoked: 'inactive',
  expired: 'inactive',
};

const displayName = (member) => {
  const name = [member.first_name, member.last_name].filter(Boolean).join(' ').trim();
  return member.email || name || member.user_id || 'Client user';
};

export default function ClientAccessTab({ clientId }) {
  const [users, setUsers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [notice, setNotice] = useState('');
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!clientId) return;
    setLoading(true);
    setLoadError('');
    try {
      const [usersResult, invitationsResult] = await Promise.all([
        listClientUsers(clientId),
        listClientInvitations(clientId),
      ]);
      setUsers(Array.isArray(usersResult?.users) ? usersResult.users : []);
      setInvitations(
        Array.isArray(invitationsResult?.invitations) ? invitationsResult.invitations : [],
      );
    } catch (e) {
      // Generic, non-leaking denial (AGENTS.md §21/§46) — never reveal whether
      // the client exists; the backend is the security boundary.
      setLoadError(
        e?.status === 403
          ? 'You do not have permission to manage client access for this organisation.'
          : e?.message || 'Unable to load client access. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => { load(); }, [load]);

  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 5000);
  };

  const onInvite = async () => {
    setActionError('');
    if (!inviteEmail.trim()) return;
    setBusy(true);
    try {
      await createClientInvitation(clientId, {
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInviteEmail('');
      setInviteRole('member');
      setShowInvite(false);
      flash('Invitation sent. Your client will receive an email to set up their access.');
      await load();
    } catch (e) {
      setActionError(e?.message || 'Unable to send the invitation. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  const onRevoke = async (invitationId) => {
    setActionError('');
    try {
      await revokeClientInvitation(clientId, invitationId);
      flash('Invitation revoked.');
      await load();
    } catch (e) {
      setActionError(e?.message || 'Unable to revoke the invitation. Please try again.');
    }
  };

  const onRoleChange = async (memberId, role) => {
    setActionError('');
    try {
      await updateClientUser(clientId, memberId, { role });
      flash('Client user access updated.');
      await load();
    } catch (e) {
      setActionError(e?.message || 'Unable to update this client user. Please try again.');
    }
  };

  const onToggleActive = async (member) => {
    setActionError('');
    try {
      await updateClientUser(clientId, member.id, {
        role: member.role,
        is_active: !member.is_active,
      });
      flash(member.is_active ? 'Client user deactivated.' : 'Client user reactivated.');
      await load();
    } catch (e) {
      setActionError(e?.message || 'Unable to update this client user. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="v3-loading"><div className="spinner" />Loading client access…</div>
    );
  }

  if (loadError) {
    return (
      <div>
        {notice && <div className="v3-note">{notice}</div>}
        <div className="v3-admin-card" data-testid="client-access-unavailable">
          <h2>Client Access</h2>
          <div className="v3-error" style={{ marginBottom: 14 }}>{loadError}</div>
          <button className="v3-btn" onClick={load}>Try again</button>
        </div>
      </div>
    );
  }

  return (
    <div className="v3-client-access" data-testid="client-access">
      {actionError && <div className="v3-error" style={{ marginBottom: 14 }}>{actionError}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-admin-card">
        <div className="v3-admin-header">
          <div>
            <h2 style={{ margin: 0 }}>Client Access</h2>
            <p className="v3-muted">
              Invite your client to access their CarbonTally dashboard and manage
              authorised client users.
            </p>
          </div>
          <button
            className="v3-btn v3-btn-primary"
            onClick={() => setShowInvite((open) => !open)}
            aria-expanded={showInvite}
          >
            + Invite Client
          </button>
        </div>

        {showInvite && (
          <div className="v3-admin-card" style={{ marginTop: 14 }} data-testid="invite-client-form">
            <h3 style={{ marginTop: 0 }}>Invite Client</h3>
            <div className="v3-admin-actions" style={{ marginTop: 0 }}>
              <label className="v3-field">
                <span className="v3-muted">Email address</span>
                <input
                  className="v3-search-input"
                  type="email"
                  placeholder="client@example.com"
                  aria-label="Client email address"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
              </label>
              <label className="v3-field">
                <span className="v3-muted">Client access</span>
                <select
                  className="v3-role-select"
                  aria-label="Client access level"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                >
                  {CLIENT_ROLES.map((role) => (
                    <option key={role.id} value={role.id}>{role.label}</option>
                  ))}
                </select>
              </label>
              <button
                className="v3-btn v3-btn-primary"
                onClick={onInvite}
                disabled={!inviteEmail.trim() || busy}
              >
                Send Invitation
              </button>
            </div>
            <p className="v3-muted">
              {CLIENT_ROLES.find((role) => role.id === inviteRole)?.description}
            </p>
          </div>
        )}
      </div>

      <div className="v3-admin-card">
        <h2>Pending Invitations</h2>
        {invitations.length === 0 ? (
          <div className="v3-empty" style={{ padding: 24 }}>
            <p style={{ marginTop: 0 }}>No invitations yet.</p>
            <p className="v3-muted">
              Invite your client by email to give them access to their CarbonTally dashboard.
            </p>
          </div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Access</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {invitations.map((invitation) => {
                const state = invitation.state || invitation.status || 'pending';
                return (
                  <tr key={invitation.id}>
                    <td>{invitation.email}</td>
                    <td>{roleLabel(invitation.role)}</td>
                    <td>
                      <span className={`v3-badge ${STATE_BADGE[state] || state}`}>{state}</span>
                    </td>
                    <td>
                      {state === 'pending' ? (
                        <button
                          className="v3-btn v3-btn-sm"
                          onClick={() => onRevoke(invitation.id)}
                        >
                          Revoke
                        </button>
                      ) : (
                        <span className="v3-muted">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <div className="v3-admin-card">
        <h2>Client Users</h2>
        {users.length === 0 ? (
          <div className="v3-empty" style={{ padding: 24 }}>
            No client users yet. Invite your client by email to give them access.
          </div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Access</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((member) => (
                <tr key={member.id}>
                  <td>
                    <div>{displayName(member)}</div>
                    {member.email && displayName(member) !== member.email && (
                      <div className="v3-muted">{member.email}</div>
                    )}
                  </td>
                  <td>
                    <select
                      className="v3-role-select"
                      aria-label={`Access for ${displayName(member)}`}
                      value={member.role}
                      onChange={(e) => onRoleChange(member.id, e.target.value)}
                    >
                      {CLIENT_ROLES.map((role) => (
                        <option key={role.id} value={role.id}>{role.label}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <span className={`v3-badge ${member.is_active ? 'active' : 'inactive'}`}>
                      {member.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="v3-btn v3-btn-sm"
                      onClick={() => onToggleActive(member)}
                    >
                      {member.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
