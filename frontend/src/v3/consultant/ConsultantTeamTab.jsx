// frontend/src/v3/consultant/ConsultantTeamTab.jsx
// CL-61 — consultant team roster + internal tasks.
// Team membership is a firm-level authorization surface: the roster is read via
// GET /api/v3/consultants/me/team and adding a member posts to the same API
// (server-enforced manage_team permission). Tasks are the firm's lightweight
// follow-up queue (type/priority/status persisted server-side).
import React, { useEffect, useState } from 'react';
import {
  addConsultantTeamMember,
  createConsultantTask,
  getConsultantTasks,
  getConsultantTeam,
  updateConsultantTaskStatus,
} from '../api';

const TASK_STATUSES = ['open', 'in_progress', 'done', 'blocked'];

export default function ConsultantTeamTab() {
  const [members, setMembers] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Add-member form
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState('consultant');
  const [adding, setAdding] = useState(false);

  // Task form
  const [taskTitle, setTaskTitle] = useState('');
  const [taskType, setTaskType] = useState('');
  const [taskPriority, setTaskPriority] = useState('medium');
  const [taskClientId, setTaskClientId] = useState('');
  const [creating, setCreating] = useState(false);

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

  useEffect(() => {
    loadTeam();
    loadTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onAddMember = async () => {
    if (!userId.trim()) return;
    setAdding(true);
    setError('');
    try {
      const created = await addConsultantTeamMember(userId.trim(), role);
      setNotice(`Team member added (role: ${created.role || role}).`);
      setUserId('');
      await loadTeam();
    } catch (e) {
      setError(e.message || 'Failed to add team member');
    } finally {
      setAdding(false);
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
        {members.length === 0 ? (
          <p className="v3-muted">No team members yet — add a consultant colleague below.</p>
        ) : (
          <table className="v3-ops-table">
            <thead><tr><th>Member</th><th>Role</th><th>Capabilities</th><th>Status</th></tr></thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id}>
                  <td>
                    <div>{displayName(m)}</div>
                    <div className="v3-muted" style={{ fontSize: 12 }}>{m.email || m.user_id}</div>
                  </td>
                  <td>{m.role}</td>
                  <td>
                    {[
                      m.can_manage_clients && 'clients',
                      m.can_upload_documents && 'upload',
                      m.can_generate_reports && 'reports',
                      m.can_manage_team && 'team',
                    ].filter(Boolean).join(', ') || '—'}
                  </td>
                  <td>{m.is_active ? 'Active' : 'Inactive'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>


      <div className="v3-admin-card">
        <h3 style={{ marginTop: 16 }}>Add team member</h3>
        <p className="v3-muted">
          Enter the user id of the existing CarbonTally user to grant them firm membership.
        </p>
        <div className="workspace-grid">
          <div className="workspace-field">
            <label>User id</label>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="00000000-0000-0000-0000-000000000000"
            />
          </div>
          <div className="workspace-field">
            <label>Role</label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="consultant">Consultant</option>
              <option value="consultant team member">Consultant team member</option>
            </select>
          </div>
        </div>
        <div className="workspace-actions">
          <button className="v3-btn primary" onClick={onAddMember} disabled={adding || !userId.trim()}>
            {adding ? 'Adding…' : 'Add team member'}
          </button>
        </div>
      </div>

      <div className="v3-admin-card">
        <h2>Firm tasks ({tasks.length})</h2>
        {tasks.length === 0 ? (
          <p className="v3-muted">No tasks yet.</p>
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
            <label>Client id (optional)</label>
            <input value={taskClientId} onChange={(e) => setTaskClientId(e.target.value)} placeholder="client uuid" />
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

