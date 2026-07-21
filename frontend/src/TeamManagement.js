import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import './TeamManagement.css';


function TeamManagement({ organization, userRole }) {
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchTeamData = async () => {
  setLoading(true);
  const { data: membersData } = await supabase.from('organization_members').select('id, role, user_id, auth.users(email)').eq('organization_id', organization.id);
  const { data: invitesData } = await supabase.from('pending_invites').select('id, email, role, created_at').eq('organization_id', organization.id);

    if (membersData) setMembers(membersData);
    if (invitesData) setInvites(invitesData);
    setLoading(false);
  };

  useEffect(() => {
    if (organization) fetchTeamData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [organization]);

  const handleInvite = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    const { error } = await supabase
      .from('pending_invites')
      .insert({ organization_id: organization.id, email: inviteEmail, role: inviteRole });

    if (error) {
      setError(error.message);
    } else {
      setMessage(`✅ Invite created for ${inviteEmail}! Tell them to sign up at CarbonTally using this exact email.`);
      setInviteEmail('');
      fetchTeamData();
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!window.confirm('Are you sure you want to remove this team member?')) return;
    
    const { error } = await supabase.from('organization_members').delete().eq('id', memberId);
    if (error) setError(error.message);
    else fetchTeamData();
  };

  const handleCancelInvite = async (inviteId) => {
    const { error } = await supabase.from('pending_invites').delete().eq('id', inviteId);
    if (error) setError(error.message);
    else fetchTeamData();
  };

  if (userRole !== 'admin') {
    return <div className="access-denied">Only Company Admins can manage the team.</div>;
  }

  return (
    <div className="team-container">
      <h2> Team Management</h2>
      
      {/* INVITE FORM */}
      <div className="invite-section">
        <h3>Invite Team Member</h3>
        <form onSubmit={handleInvite} className="invite-form">
          <input 
            type="email" 
            value={inviteEmail} 
            onChange={(e) => setInviteEmail(e.target.value)} 
            placeholder="colleague@company.com" 
            required 
          />
          <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
            <option value="viewer">Viewer (Read-only)</option>
            <option value="editor">Editor (Upload & Edit)</option>
            <option value="admin">Admin (Full Control)</option>
          </select>
          <button type="submit" className="invite-btn">Send Invite</button>
        </form>
        {message && <div className="success-msg">{message}</div>}
        {error && <div className="error-msg">{error}</div>}
        <p className="invite-hint">
          💡 <strong>How it works:</strong> Since we are using the free email tier, simply share your CarbonTally login URL with your colleague. When they sign up using the exact email address you entered above, they will automatically be added to your team with the assigned role.
        </p>
      </div>

      <div className="members-section">
        <h3>Current Team Members ({members.length})</h3>
        
        {loading ? (
          <div className="skeleton-table-container" style={{ marginTop: '1rem' }}>
            {/* Skeleton for Table Headers */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', paddingLeft: '0.5rem' }}>
              <div className="skeleton skeleton-text" style={{ width: '40%', height: '20px' }}></div>
              <div className="skeleton skeleton-text" style={{ width: '20%', height: '20px' }}></div>
              <div className="skeleton skeleton-text" style={{ width: '20%', height: '20px' }}></div>
            </div>
            
            {/* Skeleton for Table Rows */}
            {[1, 2, 3].map((i) => (
              <div key={i} style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem', alignItems: 'center', paddingLeft: '0.5rem' }}>
                <div className="skeleton skeleton-text" style={{ width: '40%', height: '24px' }}></div>
                <div className="skeleton skeleton-text" style={{ width: '20%', height: '24px', borderRadius: '999px' }}></div>
                <div className="skeleton skeleton-text" style={{ width: '20%', height: '32px', borderRadius: '6px' }}></div>
              </div>
            ))}
          </div>
        ) : (
          <table className="team-table">
            <thead>
              <tr><th>Email</th><th>Role</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.id}>
                  <td>{member.auth?.users?.email || 'Unknown'}</td>
                  <td><span className={`role-badge ${member.role}`}>{member.role}</span></td>
                  <td>
                    {member.role !== 'admin' && (
                      <button onClick={() => handleRemoveMember(member.id)} className="remove-btn">Remove</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* PENDING INVITES */}
      {invites.length > 0 && (
        <div className="invites-section">
          <h3>Pending Invites ({invites.length})</h3>
          <table className="team-table">
            <thead>
              <tr><th>Email</th><th>Proposed Role</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {invites.map((invite) => (
                <tr key={invite.id}>
                  <td>{invite.email}</td>
                  <td><span className={`role-badge ${invite.role}`}>{invite.role}</span></td>
                  <td>
                    <button onClick={() => handleCancelInvite(invite.id)} className="cancel-btn">Cancel</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default TeamManagement;