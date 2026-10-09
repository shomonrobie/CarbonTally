// frontend/src/v3/consultant/ConsultantTeamTab.jsx
// CL-61 — consultant team roster + internal tasks.
// Team membership is a firm-level authorization surface: the roster is read via
// GET /api/v3/consultants/me/team and adding a member posts to the same API
// (server-enforced manage_team permission). Tasks are the firm's lightweight
// follow-up queue (type/priority/status persisted server-side).
//
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A — human-UX cleanup:
//   UX-11/AC-14 — members are added by EMAIL (an existing CarbonTally user),
//                 never by an internal user id;
//   UX-13/AC-16 — the role list is the REAL backend role vocabulary, with copy
//                 distinguishing role (classification) from capabilities;
//   UX-15..19   — Firm tasks are described by their actual semantics and the
//                 optional client link is a human-readable SELECT of the
//                 consultant's authorised clients, not a raw UUID field.
import React, { useEffect, useState } from 'react';
import {
  addConsultantTeamMember,
  createConsultantTask,
  deactivateConsultantTeamMember,
  getConsultantTasks,
  getConsultantTeam,
  listConsultantClients,
  reactivateConsultantTeamMember,
  updateConsultantTaskStatus,
  updateConsultantTeamMemberCapabilities,
} from '../api';
import { supabase } from '../../supabaseClient';

const TASK_STATUSES = ['open', 'in_progress', 'done', 'blocked'];

// CT-CONSULTANT-MODEL-IMPLEMENTATION-03 (P5) — the operational capabilities the
// firm may administer. Commercial entitlement (plan/seats/mode/white-label) is
// deliberately NOT in this list: it is CarbonTally-Admin-controlled (PO-5) and
// the backend rejects any such field (422). The server response is authoritative.
const CAPABILITY_FIELDS = [
  ['can_view_client', 'View client (admission)'],
  ['can_approve', 'Approve (final)'],
  ['can_manage_clients', 'Manage clients'],
  ['can_manage_team', 'Manage team'],
  ['can_upload_documents', 'Upload documents'],
  ['can_generate_reports', 'Generate reports'],
  ['can_extract', 'Extract'],
  ['can_map', 'Map factors'],
  ['can_validate', 'Validate'],
  ['can_calculate', 'Calculate'],
  ['can_confirm_automation', 'Confirm automation'],
  ['can_submit', 'Submit'],
];

// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A (UX-13/AC-16) — the REAL firm role
// vocabulary the backend accepts (backend/api/consultant_auth.py:CONSULTANT_ROLES).
// The previous UI offered a "Consultant team member" value the API rejects (422).
// Role is a firm CLASSIFICATION only; a member's access is governed by the
// capabilities above, which the server enforces (RBAC ∩ capabilities).
const ROLE_OPTIONS = [
  ['consultant', 'Consultant'],
  ['manager', 'Manager'],
  ['viewer', 'Viewer'],
  ['owner', 'Owner'],
];

const roleLabel = (value) => {
  const found = ROLE_OPTIONS.find(([v]) => v === value);
  return found ? found[1] : value;
};

export default function ConsultantTeamTab() {
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [clients, setClients] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Add-member form (CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A UX-11/AC-14 —
  // human-readable identity: email, not an internal user id).
  const [memberEmail, setMemberEmail] = useState('');
  const [role, setRole] = useState('consultant');
  const [adding, setAdding] = useState(false);

  // Task form
  const [taskTitle, setTaskTitle] = useState('');
  const [taskType, setTaskType] = useState('');
  const [taskPriority, setTaskPriority] = useState('medium');
  const [taskClientId, setTaskClientId] = useState('');
  const [creating, setCreating] = useState(false);

  // CT03 (P1/P5) — capability administration state.
  const [currentUserId, setCurrentUserId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [capDraft, setCapDraft] = useState({});
  const [savingCaps, setSavingCaps] = useState(false);

  useEffect(() => {
    let active = true;
    supabase.auth.getUser().then(({ data }) => {
      if (active) setCurrentUserId(data?.user?.id || null);
    });
    return () => { active = false; };
  }, []);

  // The caller may administer capabilities only when their OWN roster row holds
  // can_manage_team (mirrors the server's CAP-MANAGE-TEAM rule). The backend is
  // still the boundary — this only decides whether to offer the control.
  const ownRow = members.find((m) => m.user_id === currentUserId) || null;
  const canAdminister = Boolean(ownRow && ownRow.can_manage_team);

  const startEditCapabilities = (member) => {
    setEditingId(member.id);
    setCapDraft(
      CAPABILITY_FIELDS.reduce((acc, [key]) => {
        acc[key] = Boolean(member[key]);
        return acc;
      }, {})
    );
  };

  const cancelEditCapabilities = () => {
    setEditingId(null);
    setCapDraft({});
  };

  const saveCapabilities = async (member) => {
    setSavingCaps(true);
    setError('');
    setNotice('');
    try {
      await updateConsultantTeamMemberCapabilities(member.id, capDraft);
      setNotice('Capabilities updated (server-confirmed).');
      setEditingId(null);
      setCapDraft({});
      await loadTeam();
    } catch (e) {
      setError(e.message || 'Failed to update capabilities');
    } finally {
      setSavingCaps(false);
    }
  };

  const loadTeam = async () => {
    try {
      const result = await getConsultantTeam();
      setMembers(result.members || []);
    } catch (e) {
      setError(e.message || 'Failed to load team');
    }
  };

  const loadTasks = async () => {
    try {
      const result = await getConsultantTasks();
      setTasks(result.tasks || []);
    } catch (e) {
      setError(e.message || 'Failed to load tasks');
    }
  };

  // CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A (UX-16/AC-18) — the authorised
  // client set for the optional task client link. A failure here must not block
  // the team/tasks surfaces (the field simply offers no clients).
  const loadClients = async () => {
    try {
      const result = await listConsultantClients();
      setClients(result.clients || []);
    } catch (_e) {
      setClients([]);
    }
  };

  useEffect(() => {
    loadTeam();
    loadTasks();
    loadClients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onAddMember = async () => {
    const email = memberEmail.trim().toLowerCase();
    if (!email) return;
    setAdding(true);
    setError('');
    try {
      const created = await addConsultantTeamMember({ email, role });
      setNotice(`Team member added (${email}, role: ${created.role || role}).`);
      setMemberEmail('');
      await loadTeam();
    } catch (e) {
      setError(e.message || 'Failed to add team member');
    } finally {
      setAdding(false);
    }
  };

  const onToggleMemberActive = async (member, deactivate) => {
    setError('');
    setNotice('');
    if (deactivate && !window.confirm(
      `Revoke consultant access for this team member? Their client access ends immediately (server-side).`
    )) return;
    try {
      if (deactivate) {
        await deactivateConsultantTeamMember(member.id);
        setNotice('Team member access revoked.');
      } else {
        await reactivateConsultantTeamMember(member.id);
        setNotice('Team member access restored.');
      }
      await loadTeam();
    } catch (e) {
      setError(e.message || 'Failed to update team member');
    }
  };

  const onCreateTask = async () => {
    if (!taskTitle.trim()) return;
    setCreating(true);
    setError('');
    try {
      await createConsultantTask({
        task_title: taskTitle.trim(),
        task_type: taskType.trim() || null,
        priority: taskPriority || null,
        client_id: taskClientId.trim() || null,
      });
      setNotice('Task created.');
      setTaskTitle('');
      setTaskType('');
      setTaskPriority('medium');
      setTaskClientId('');
      await loadTasks();
    } catch (e) {
      setError(e.message || 'Failed to create task');
    } finally {
      setCreating(false);
    }
  };

  const onTaskStatus = async (taskId, status) => {
    try {
      await updateConsultantTaskStatus(taskId, status);
      await loadTasks();
    } catch (e) {
      setError(e.message || 'Failed to update task');
    }
  };

  const displayName = (m) =>
    [m.first_name, m.last_name].filter(Boolean).join(' ') || m.email || m.user_id;

  return (
    <div>
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="v3-admin-card">
        <h2>Team roster ({members.length})</h2>
        <p className="v3-muted">
          Role is each member&apos;s firm classification. Capabilities are what the
          member may actually do, and the server enforces them — a role alone
          grants nothing.
        </p>
        {members.length === 0 ? (
          <p className="v3-muted">No team members yet — add a consultant colleague below.</p>
        ) : (
          <table className="v3-ops-table">
            <thead><tr><th>Member</th><th>Role</th><th>Capabilities</th><th>Status</th><th /></tr></thead>
            <tbody>
              {members.map((m) => (
                <React.Fragment key={m.id}>
                  <tr>
                    <td>
                      <div>{displayName(m)}</div>
                      <div className="v3-muted" style={{ fontSize: 12 }}>{m.email || m.user_id}</div>
                    </td>
                    <td>{roleLabel(m.role)}</td>
                    <td>
                      {[
                        m.can_view_client && 'view client',
                        m.can_approve && 'approve',
                        m.can_manage_clients && 'clients',
                        m.can_manage_team && 'team',
                        m.can_upload_documents && 'upload',
                        m.can_generate_reports && 'reports',
                        m.can_extract && 'extract',
                        m.can_map && 'map',
                        m.can_validate && 'validate',
                        m.can_calculate && 'calculate',
                        m.can_confirm_automation && 'confirm automation',
                        m.can_submit && 'submit',
                      ].filter(Boolean).join(', ') || '—'}
                    </td>
                    <td>{m.is_active ? 'Active' : 'Revoked'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {canAdminister && m.user_id !== currentUserId && (
                          <button
                            className="v3-btn v3-btn-sm"
                            onClick={() => startEditCapabilities(m)}
                          >
                            Edit capabilities
                          </button>
                        )}
                        {m.is_active ? (
                          <button className="v3-btn v3-btn-sm" onClick={() => onToggleMemberActive(m, true)}>Revoke access</button>
                        ) : (
                          <button className="v3-btn v3-btn-sm" onClick={() => onToggleMemberActive(m, false)}>Reactivate</button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {editingId === m.id && (
                    <tr>
                      <td colSpan={5}>
                        <div className="v3-muted" style={{ marginBottom: 8 }}>
                          Capabilities for {displayName(m)}. A consultant cannot change
                          their own set; the server enforces this and records the change.
                        </div>
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
                            gap: 8,
                          }}
                        >
                          {CAPABILITY_FIELDS.map(([key, label]) => (
                            <label key={key} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                              <input
                                type="checkbox"
                                checked={Boolean(capDraft[key])}
                                onChange={(e) =>
                                  setCapDraft((d) => ({ ...d, [key]: e.target.checked }))
                                }
                              />
                              {label}
                            </label>
                          ))}
                        </div>
                        <div className="workspace-actions">
                          <button
                            className="v3-btn primary v3-btn-sm"
                            onClick={() => saveCapabilities(m)}
                            disabled={savingCaps}
                          >
                            {savingCaps ? 'Saving…' : 'Save capabilities'}
                          </button>
                          <button className="v3-btn v3-btn-sm" onClick={cancelEditCapabilities}>
                            Cancel
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>


      <div className="v3-admin-card">
        <h3 style={{ marginTop: 16 }}>Add team member</h3>
        <p className="v3-muted">
          Add an existing CarbonTally user to your firm by email address. The
          account is matched server-side; the new member starts with no
          operational capabilities until you grant them below.
        </p>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label htmlFor="team-member-email">Email</label>
            <input
              id="team-member-email"
              type="email"
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              placeholder="jane@yourfirm.example"
              autoComplete="off"
            />
          </div>
          <div className="workspace-field">
            <label htmlFor="team-member-role">Role</label>
            <select
              id="team-member-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              {ROLE_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            <div className="v3-muted" style={{ fontSize: 12 }}>
              A role is a classification only — capabilities govern access.
            </div>
          </div>
        </div>
        <div className="workspace-actions">
          <button className="v3-btn primary" onClick={onAddMember} disabled={adding || !memberEmail.trim()}>
            {adding ? 'Adding…' : 'Add team member'}
          </button>
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Firm tasks ({tasks.length})</h2>
        <p className="v3-muted">
          Internal follow-up tasks for your firm. Optionally link a task to one of
          your clients; tasks are visible to your firm&apos;s members only.
        </p>
        {tasks.length === 0 ? (
          <p className="v3-muted">No firm tasks yet — create one below.</p>
        ) : (
          <table className="v3-ops-table">
            <thead><tr><th>Task</th><th>Type</th><th>Priority</th><th>Status</th><th /></tr></thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td>{t.task_title}</td>
                  <td>{t.task_type || '—'}</td>
                  <td>{t.priority || '—'}</td>
                  <td>{t.status}</td>
                  <td>
                    <select
                      value={t.status}
                      onChange={(e) => onTaskStatus(t.id, e.target.value)}
                    >
                      {TASK_STATUSES.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <h3 style={{ marginTop: 16 }}>New task</h3>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label>Task title</label>
            <input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="e.g. Process April utility bills" />
          </div>
          <div className="workspace-field">
            <label>Type</label>
            <input value={taskType} onChange={(e) => setTaskType(e.target.value)} placeholder="e.g. processing" />
          </div>
          <div className="workspace-field">
            <label>Priority</label>
            <select value={taskPriority} onChange={(e) => setTaskPriority(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div className="workspace-field">
            <label htmlFor="task-client">Client (optional)</label>
            <select
              id="task-client"
              value={taskClientId}
              onChange={(e) => setTaskClientId(e.target.value)}
              aria-label="Client (optional)"
            >
              <option value="">— No specific client —</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.client_name}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="workspace-actions">
          <button className="v3-btn primary" onClick={onCreateTask} disabled={creating || !taskTitle.trim()}>
            {creating ? 'Creating…' : 'Create task'}
          </button>
        </div>
      </div>
    </div>
  );
}

