// frontend/src/v3/admin/MembersTab.jsx
// Members + invitations using the V3 org-scoped backend (real data).
import React, { useCallback, useEffect, useState } from 'react';
import {
  addMember,
  createInvitation,
  listInvitations,
  listMembers,
  removeMember,
  revokeInvitation,
  updateMember,
} from '../api';

const ROLE_IDS = ['owner', 'admin', 'member', 'viewer'];

export default function MembersTab({ organization, roles }) {
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [newMemberUserId, setNewMemberUserId] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('member');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [confirmRemove, setConfirmRemove] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [membersResult, invitationsResult] = await Promise.all([
        listMembers(organization.id),
        listInvitations(organization.id).catch(() => ({ invitations: [] })),
      ]);
      setMembers(membersResult.members || []);
      setInvitations(invitationsResult.invitations || []);
    } catch (e) {
      setError(e.message || 'Failed to load members');
    } finally {
      setLoading(false);
    }
  }, [organization.id]);

  useEffect(() => { load(); }, [load]);

  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 5000);
  };

  const onRoleChange = async (memberId, role) => {
    try {
      await updateMember(memberId, { role });
      flash('Member role updated.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to update role');
    }
  };

  const onAddMember = async () => {
    setError('');
    try {
      await addMember(organization.id, { user_id: newMemberUserId.trim(), role: newMemberRole });
      setNewMemberUserId('');
      flash('Member added.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to add member');
    }
  };

  const onRemoveMember = async (memberId) => {
    setError('');
    try {
      await removeMember(memberId);
      setConfirmRemove(null);
      flash('Member removed.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to remove member');
    }
  };

  const onInvite = async () => {
    setError('');
    try {
      await createInvitation(organization.id, { email: inviteEmail.trim(), role: inviteRole });
      setInviteEmail('');
      flash('Invitation created.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to create invitation');
    }
  };

  const onRevokeInvitation = async (invitationId) => {
    try {
      await revokeInvitation(invitationId);
      flash('Invitation revoked.');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to revoke invitation');
    }
  };

  const roleOptions = roles.length ? roles : ROLE_IDS.map((id) => ({ id, name: id, description: id }));

  return (
    <div>
      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-admin-card">
        <h2>Roles</h2>
        <p className="v3-muted">
          The V3 customer role model (from the organization_members role constraint):
        </p>
        <div className="v3-meta-list">
          {roleOptions.map((role) => (
            <div className="v3-meta-item" key={role.id}>
              <div className="k">{role.name}</div>
              <div className="v">{role.description || role.id}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Members</h2>
        {loading ? (
          <div className="v3-loading"><div className="spinner" />Loading members…</div>
        ) : members.length === 0 ? (
          <div className="v3-empty">No members yet.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.id}>
                  <td>
                    <div>{member.email || member.user_id}</div>
                    {member.first_name && (
                      <div className="v3-muted">{member.first_name} {member.last_name || ''}</div>
                    )}
                  </td>
                  <td>
                    <select
                      className="v3-role-select"
                      value={member.role}
                      onChange={(e) => onRoleChange(member.id, e.target.value)}
                    >
                      {ROLE_IDS.map((role) => <option key={role} value={role}>{role}</option>)}
                    </select>
                  </td>
                  <td>
                    <span className={`v3-badge ${member.is_active ? 'active' : 'inactive'}`}>
                      {member.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="v3-muted">{member.created_at || '—'}</td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => setConfirmRemove(member)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="v3-admin-actions">
          <input
            className="v3-search-input"
            placeholder="user id"
            value={newMemberUserId}
            onChange={(e) => setNewMemberUserId(e.target.value)}
          />
          <select className="v3-role-select" value={newMemberRole} onChange={(e) => setNewMemberRole(e.target.value)}>
            {ROLE_IDS.map((role) => <option key={role} value={role}>{role}</option>)}
          </select>
          <button className="v3-btn v3-btn-primary" onClick={onAddMember} disabled={!newMemberUserId.trim()}>
            Add member
          </button>
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Invitations</h2>
        <div className="v3-admin-actions" style={{ marginTop: 0, marginBottom: 14 }}>
          <input
            className="v3-search-input"
            placeholder="email"
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <select className="v3-role-select" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
            {ROLE_IDS.map((role) => <option key={role} value={role}>{role}</option>)}
          </select>
          <button className="v3-btn v3-btn-primary" onClick={onInvite} disabled={!inviteEmail.trim()}>
            Send invitation
          </button>
        </div>
        {invitations.length === 0 ? (
          <div className="v3-empty" style={{ padding: 24 }}>No invitations yet.</div>
        ) : (
          <table className="v3-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invitations.map((invitation) => (
                <tr key={invitation.id}>
                  <td>{invitation.email}</td>
                  <td><span className={`v3-badge ${invitation.status}`}>{invitation.status}</span></td>
                  <td className="v3-muted">{invitation.expires_at || '—'}</td>
                  <td>
                    {invitation.status === 'pending' && (
                      <button className="v3-btn v3-btn-sm" onClick={() => onRevokeInvitation(invitation.id)}>
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {confirmRemove && (
        <div className="v3-modal-backdrop" onClick={() => setConfirmRemove(null)}>
          <div className="v3-modal v3-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Remove member?</h2>
            <p className="v3-muted">
              {confirmRemove.email || confirmRemove.user_id} will lose access to {organization.name}. This action is immediate.
            </p>
            <div className="v3-modal-actions">
              <button className="v3-btn" onClick={() => setConfirmRemove(null)}>Cancel</button>
              <button className="v3-btn v3-btn-danger" onClick={() => onRemoveMember(confirmRemove.id)}>
                Remove member
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
