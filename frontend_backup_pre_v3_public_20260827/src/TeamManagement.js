// TeamManagement.jsx - Complete with Backend API

import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import './css/TeamManagement.css';
import toast from 'react-hot-toast';

function TeamManagement({ organization, userRole }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [sending, setSending] = useState(false);
  const isAdmin = userRole === 'admin';

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || localStorage.getItem('access_token');
  };

  const fetchMembers = async () => {
    setLoading(true);
    const token = await getToken();

    try {
      const response = await fetch(
        `${API_URL}/api/organizations/team/${organization.id}/members`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        setMembers(result.members || []);
        console.log('✅ Team members loaded:', result.members?.length || 0);
      } else {
        console.error('Failed to fetch members:', response.status);
        toast.error('Failed to load team members');
        setMembers([]);
      }
    } catch (error) {
      console.error('Error fetching members:', error);
      toast.error('Failed to load team members');
      setMembers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organization?.id) {
      fetchMembers();
    }
  }, [organization?.id]);

  const handleInvite = async (e) => {
    e.preventDefault();
    
    if (!inviteEmail) {
      toast.error('Please enter an email address');
      return;
    }

    setSending(true);
    const token = await getToken();

    try {
      const response = await fetch(
        `${API_URL}/api/organizations/team/${organization.id}/invite`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            email: inviteEmail,
            role: inviteRole,
          }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        toast.success(`✅ ${inviteEmail} invited as ${inviteRole}!`);
        setInviteEmail('');
        setInviteRole('viewer');
        fetchMembers();
      } else {
        toast.error(result.detail || 'Failed to invite member');
      }
    } catch (error) {
      console.error('Error inviting member:', error);
      toast.error('Failed to invite member');
    } finally {
      setSending(false);
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;

    const token = await getToken();

    try {
      const response = await fetch(
        `${API_URL}/api/organizations/team/${organization.id}/members/${memberId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        toast.success('Member removed successfully');
        fetchMembers();
      } else {
        const result = await response.json();
        toast.error(result.detail || 'Failed to remove member');
      }
    } catch (error) {
      console.error('Error removing member:', error);
      toast.error('Failed to remove member');
    }
  };

  const handleUpdateRole = async (memberId, newRole) => {
    const token = await getToken();

    try {
      const response = await fetch(
        `${API_URL}/api/organizations/team/${organization.id}/members/${memberId}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ role: newRole }),
        }
      );

      if (response.ok) {
        toast.success('Role updated successfully');
        fetchMembers();
      } else {
        const result = await response.json();
        toast.error(result.detail || 'Failed to update role');
      }
    } catch (error) {
      console.error('Error updating role:', error);
      toast.error('Failed to update role');
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      admin: 'bg-red-100 text-red-800',
      editor: 'bg-blue-100 text-blue-800',
      viewer: 'bg-gray-100 text-gray-800',
    };
    return colors[role] || colors.viewer;
  };

  const getRoleDisplayName = (role) => {
    const names = {
      admin: 'Admin',
      editor: 'Editor',
      viewer: 'Viewer',
    };
    return names[role] || role;
  };

  if (loading) {
    return (
      <div className="team-management-container">
        <div className="skeleton skeleton-text title" style={{ width: '30%', marginBottom: '1.5rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
        <div className="skeleton skeleton-box" style={{ height: '60px', marginBottom: '1rem' }}></div>
      </div>
    );
  }

  return (
    <div className="team-management-container">
      <h2>👥 Team Management</h2>
      <p className="subtitle">Invite team members and manage their access to your organization.</p>

      {!isAdmin && (
        <div className="info-banner">
          ⚠️ You have view-only access. Only organization admins can manage team members.
        </div>
      )}

      {isAdmin && (
        <div className="invite-section">
          <h3>Invite Team Member</h3>
          <form onSubmit={handleInvite} className="invite-form">
            <input
              type="email"
              placeholder="colleague@company.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
              disabled={sending}
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              disabled={sending}
            >
              <option value="viewer">Viewer (Read-only)</option>
              <option value="editor">Editor (Can edit data)</option>
              <option value="admin">Admin (Full access)</option>
            </select>
            <button type="submit" className="invite-btn" disabled={sending}>
              {sending ? '⏳ Sending...' : 'Send Invite'}
            </button>
          </form>
          <p className="hint">
            💡 Users must already have a CarbonTally account. They will be added to your team immediately.
          </p>
        </div>
      )}

      <div className="members-section">
        <h3>Current Team Members ({members.length})</h3>
        
        {members.length === 0 ? (
          <p className="empty-msg">No team members yet.</p>
        ) : (
          <div className="members-table">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                <tr key={member.id}>
                  <td>
                    <div className="member-info">
                      <div className="member-avatar">
                        {member.full_name?.[0] || member.email?.[0]?.toUpperCase() || '?'}
                      </div>
                      <div>
                        <div className="member-name">
                          {member.full_name || 'Team Member'}
                        </div>
                        <div className="member-email">
                          {member.email || `User ${member.user_id.slice(0, 8)}`}
                        </div>
                        <div className="member-status">
                          {member.is_active ? '🟢 Active' : '🔴 Inactive'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td>
                    {isAdmin ? (
                      <select
                        value={member.role}
                        onChange={(e) => handleUpdateRole(member.id, e.target.value)}
                        className={`role-select ${getRoleBadgeColor(member.role)}`}
                      >
                        <option value="viewer">Viewer</option>
                        <option value="editor">Editor</option>
                        <option value="admin">Admin</option>
                      </select>
                    ) : (
                      <span className={`role-badge ${getRoleBadgeColor(member.role)}`}>
                        {getRoleDisplayName(member.role)}
                      </span>
                    )}
                  </td>
                  <td>
                    {isAdmin && member.role !== 'admin' && (
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        className="remove-btn"
                        title="Remove member"
                      >
                        ✕
                      </button>
                    )}
                    {isAdmin && member.role === 'admin' && (
                      <span className="admin-badge">👑 Admin</span>
                    )}
                  </td>
                </tr>
              ))}


              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default TeamManagement;