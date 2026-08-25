// frontend/src/v3/admin/SecurityTab.jsx
// Security settings using the existing Supabase Auth architecture.
//
// - Authentication provider / account info: real data from the Supabase user.
// - Change password: uses supabase.auth.updateUser (existing auth, not custom).
// - MFA/TOTP: CarbonTally has no MFA backend/UI surface; the Supabase platform
//   MFA tables exist but MFA enablement cannot be verified here, so this tab
//   reports the documented limitation instead of a fake enrollment flow.
import React, { useEffect, useState } from 'react';
import { supabase } from '../../supabaseClient';

export default function SecurityTab() {
  const [user, setUser] = useState(null);
  const [provider, setProvider] = useState('email');
  const [identities, setIdentities] = useState([]);
  const [mfaStatus, setMfaStatus] = useState('unknown');
  const [mfaDetail, setMfaDetail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const { data: { user: current } } = await supabase.auth.getUser();
        if (!current) return;
        setUser(current);
        setProvider(current.app_metadata?.provider || 'email');
        setIdentities(current.identities || []);
      } catch (e) {
        setError(e.message || 'Failed to load account info');
      }
      // MFA status — real query; the limitation is surfaced if unavailable.
      try {
        const { data, error: mfaError } = await supabase.auth.mfa.listFactors();
        if (mfaError) {
          setMfaStatus('unavailable');
          setMfaDetail(mfaError.message || 'MFA is not enabled for this account/project.');
        } else if (data?.factors?.length) {
          setMfaStatus('enrolled');
          setMfaDetail(`${data.factors.length} factor(s) enrolled.`);
        } else {
          setMfaStatus('not-enrolled');
          setMfaDetail('No MFA factors enrolled.');
        }
      } catch (e) {
        setMfaStatus('unavailable');
        setMfaDetail('MFA is not available in this environment.');
      }
    };
    load();
  }, []);

  const onChangePassword = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const { error: updateError } = await supabase.auth.updateUser({
        password: newPassword,
      });
      if (updateError) throw new Error(updateError.message);
      setNewPassword('');
      setNotice('Password updated successfully.');
      setTimeout(() => setNotice(''), 5000);
    } catch (e) {
      setError(e.message || 'Failed to update password');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-admin-card">
        <h2>Account</h2>
        <div className="v3-meta-list">
          <div className="v3-meta-item">
            <div className="k">Email</div>
            <div className="v">{user?.email || '—'}</div>
          </div>
          <div className="v3-meta-item">
            <div className="k">User ID</div>
            <div className="v">{user?.id || '—'}</div>
          </div>
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Authentication provider</h2>
        <p className="v3-muted">
          Authentication uses the existing Supabase Auth architecture. No custom
          authentication is used and no credentials are stored in the frontend.
        </p>
        <div className="v3-meta-list">
          <div className="v3-meta-item">
            <div className="k">Sign-in provider</div>
            <div className="v">{provider || 'email'}</div>
          </div>
        </div>
        {identities.length > 0 && (
          <table className="v3-table" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Identity</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {identities.map((identity) => (
                <tr key={identity.id}>
                  <td>{identity.provider}</td>
                  <td>{identity.identity_data?.email || identity.id}</td>
                  <td className="v3-muted">{identity.created_at || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="v3-admin-card">
        <h2>Password</h2>
        <p className="v3-muted">Change your password through Supabase Auth (existing authentication architecture).</p>
        <div className="v3-form-group" style={{ maxWidth: 320 }}>
          <label>New password</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="••••••••"
          />
          <p className="v3-form-hint">Min 6 characters (Supabase Auth password policy).</p>
        </div>
        <div className="v3-admin-actions">
          <button
            className="v3-btn v3-btn-primary"
            onClick={onChangePassword}
            disabled={busy || newPassword.length < 6}
          >
            {busy ? 'Updating…' : 'Update password'}
          </button>
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Multi-factor authentication (MFA / TOTP)</h2>
        {mfaStatus === 'unavailable' ? (
          <div className="v3-note warn">
            MFA/TOTP is not available in this environment. CarbonTally has no MFA
            backend/UI surface yet; the Supabase Auth platform MFA tables exist,
            but MFA enablement cannot be verified here. This is a documented
            limitation (follow-on work), not a functional MFA interface.
          </div>
        ) : (
          <div className="v3-note">
            MFA status: <strong>{mfaStatus}</strong>. {mfaDetail}
          </div>
        )}
      </div>
    </div>
  );
}
