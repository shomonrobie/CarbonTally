// frontend/src/v3/ops/BackupsTab.jsx
// BACKUP-01/02 — Admin Backups area (architecture §9, "Admin Backup History").
//
// A thin read/write surface over /api/v3/admin/backups. Everything shown is the
// backend's own payload — job metadata, the effective policy and the
// non-secret destination description. Nothing is derived or invented here, and
// this component is NOT an authorization boundary: the backend re-checks admin
// authority AND the `can_manage_backups` capability on every call (§9).
//
// Deliberately absent: any one-click production restore. §9 keeps restore
// strictly outside the normal admin surface; the recovery procedure is run by
// an operator under stronger authorization.
import React, { useCallback, useEffect, useState } from 'react';
import {
  createBackup,
  downloadBackupArtifact,
  getBackupPair,
  getBackupPolicy,
  getBackupStatus,
  listBackups,
  updateBackupPolicy,
  verifyBackup,
} from '../api';
import {
  Alert,
  Button,
  Card,
  ConfirmationDialog,
  LoadingState,
  StatCard,
} from '../components/ui';
import DataTable from '../components/ui/DataTable';

const KIND_LABELS = { database: 'Database', objects: 'Storage objects' };
const FREQUENCIES = ['manual', 'daily', 'weekly'];
const VERIFY_LABELS = {
  verified: 'Verified',
  failed: 'Failed',
  unverified: 'Not verified',
};

const fmtStamp = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleString();
};

const fmtBytes = (n) => {
  if (n === null || n === undefined) return '—';
  const bytes = Number(n);
  if (!Number.isFinite(bytes)) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
};

// A checksum is evidence, not decoration: show enough to compare, never a
// fabricated value when the backend has not recorded one.
const fmtChecksum = (value) => (value ? `${String(value).slice(0, 12)}…` : '—');

export default function BackupsTab() {
  const [status, setStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [policyMeta, setPolicyMeta] = useState(null);
  const [form, setForm] = useState(null);
  const [pair, setPair] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');
  const [confirmCreate, setConfirmCreate] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [statusResult, listResult, policyResult] = await Promise.all([
        getBackupStatus(),
        listBackups(50, 0),
        getBackupPolicy(),
      ]);
      setStatus(statusResult.status || null);
      setJobs(listResult.backups || []);
      setPolicyMeta(policyResult);
      setForm({
        enabled: !!policyResult.policy?.enabled,
        frequency: policyResult.policy?.frequency || 'manual',
        retention_days:
          policyResult.retention_days === null ||
          policyResult.retention_days === undefined
            ? ''
            : String(policyResult.retention_days),
        object_backup_enabled: !!policyResult.policy?.object_backup_enabled,
        object_prefix: policyResult.policy?.object_prefix || '',
      });
    } catch (e) {
      setError(
        e.status === 403
          ? 'You do not have permission to manage backups.'
          : e.message || 'Unable to load backup status. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);
  const flash = (message) => {
    setNotice(message);
    setTimeout(() => setNotice(''), 6000);
  };

  const guard = (e, fallback) =>
    setError(e.status === 403 ? 'You do not have permission to manage backups.' : e.message || fallback);

  const runCreate = async () => {
    setBusy('create');
    setError('');
    try {
      const result = await createBackup({});
      setConfirmCreate(false);
      flash(result.message || 'Backup queued.');
      await load();
    } catch (e) {
      guard(e, 'Unable to create a backup.');
    } finally {
      setBusy('');
    }
  };

  const runVerify = async (job) => {
    setBusy(`verify:${job.id}`);
    setError('');
    try {
      const result = await verifyBackup(job.id);
      const verification = result.verification || {};
      flash(
        verification.verified
          ? `Job ${job.id} verified against its stored artifact.`
          : `Job ${job.id} FAILED verification: ${(verification.problems || []).join('; ') || 'see the job record'}`,
      );
      await load();
    } catch (e) {
      guard(e, 'Unable to verify this backup.');
    } finally {
      setBusy('');
    }
  };

  const runDownload = async (job) => {
    setBusy(`download:${job.id}`);
    setError('');
    try {
      const filename = await downloadBackupArtifact(job.id);
      flash(`Downloaded ${filename} (encrypted artifact; the key stays in separate custody).`);
    } catch (e) {
      guard(e, 'Unable to download this backup.');
    } finally {
      setBusy('');
    }
  };

  const runPair = async (job) => {
    setBusy(`pair:${job.id}`);
    setError('');
    try {
      setPair(await getBackupPair(job.id));
    } catch (e) {
      guard(e, 'Unable to read the backup set.');
    } finally {
      setBusy('');
    }
  };

  const savePolicy = async () => {
    if (!form) return;
    setBusy('policy');
    setError('');
    try {
      const payload = {
        enabled: !!form.enabled,
        object_backup_enabled: !!form.object_backup_enabled,
        frequency: form.frequency,
        object_prefix: form.object_prefix || '',
        retention_days:
          form.retention_days === '' ? null : Number(form.retention_days),
      };
      await updateBackupPolicy(payload);
      flash('Backup policy saved.');
      await load();
    } catch (e) {
      guard(e, 'Unable to save the backup policy.');
    } finally {
      setBusy('');
    }
  };

  if (loading && !status) {
    return <LoadingState label="Loading backup status…" />;
  }

  const counts = (status && status.counts) || {};
  const destination = (status && status.destination) || {};
  const retention = (status && status.retention) || {};
  const activeJob = status && status.active_job;

  const columns = [
    {
      key: 'requested_at',
      header: 'Requested',
      accessor: 'requested_at',
      render: (row) => fmtStamp(row.requested_at),
      isHeader: true,
    },
    {
      key: 'kind',
      header: 'Artifact',
      accessor: 'kind',
      render: (row) => KIND_LABELS[row.kind] || row.kind,
    },
    { key: 'status', header: 'State', accessor: 'status', render: (row) => row.status },
    {
      key: 'artifact_bytes',
      header: 'Size',
      accessor: 'artifact_bytes',
      render: (row) => fmtBytes(row.artifact_bytes),
    },
    {
      key: 'checksum_sha256',
      header: 'SHA-256 (ciphertext)',
      accessor: 'checksum_sha256',
      render: (row) => fmtChecksum(row.checksum_sha256),
    },
    {
      key: 'verification_status',
      header: 'Integrity',
      accessor: 'verification_status',
      render: (row) => VERIFY_LABELS[row.verification_status] || row.verification_status,
    },
    {
      key: 'expires_at',
      header: 'Expires',
      accessor: 'expires_at',
      render: (row) => fmtStamp(row.expires_at),
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (row) => {
        const completed = row.status === 'completed' && row.storage_key;
        return (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Button
              variant="secondary"
              size="sm"
              icon="check"
              disabled={!completed}
              loading={busy === `verify:${row.id}`}
              onClick={() => runVerify(row)}
            >
              Verify
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon="download"
              disabled={!completed}
              loading={busy === `download:${row.id}`}
              onClick={() => runDownload(row)}
            >
              Download
            </Button>
            <Button
              variant="ghost"
              size="sm"
              loading={busy === `pair:${row.id}`}
              onClick={() => runPair(row)}
            >
              Set
            </Button>
          </div>
        );
      },
    },
  ];

  return (
    <div>
      {notice && <Alert tone="success" title="Backups">{notice}</Alert>}
      {error && <Alert tone="error" title="Backup action failed">{error}</Alert>}

      <Alert tone="info" title="Backup management">
        A backup copies production data. A request only <strong>queues</strong> a job — the
        worker performs the export, encryption and upload, and the history below reports what
        actually happened. Downloads return the <strong>encrypted</strong> artifact; the key
        stays in separate custody.
      </Alert>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
        <StatCard label="Completed backups" value={counts.completed ?? '—'} />
        <StatCard label="Failed backups" value={counts.failed ?? '—'} />
        <StatCard label="Verified artifacts" value={counts.verified ?? '—'} />
        <StatCard label="Completed, not verified" value={counts.unverified_completed ?? '—'} />
      </div>

      <Card
        title="Backup system"
        actions={
          <Button
            variant="primary"
            icon="plus"
            onClick={() => setConfirmCreate(true)}
            disabled={status && status.enabled === false}
          >
            Create backup
          </Button>
        }
        style={{ marginTop: 16 }}
      >
        <div className="workspace-grid">
          <div className="workspace-field">
            <strong>Policy</strong>
            <div>{status && status.enabled ? 'Enabled' : 'Disabled'}</div>
          </div>
          <div className="workspace-field">
            <strong>Retention</strong>
            <div>
              {retention.days === null || retention.days === undefined
                ? 'Not configured (no expiry)'
                : `${retention.days} days`}
            </div>
          </div>
          <div className="workspace-field">
            <strong>Preferred frequency</strong>
            <div>{status?.scheduling?.configured_intent || '—'} (recorded intent only)</div>
          </div>
          <div className="workspace-field">
            <strong>Destination</strong>
            <div>
              {destination.provider || '—'}
              {destination.bucket ? ` · ${destination.bucket}` : ''}
              {destination.prefix ? ` · ${destination.prefix}` : ''}
            </div>
          </div>
          <div className="workspace-field">
            <strong>Encryption</strong>
            <div>
              {destination.encryption || '—'}
              {destination.key_id ? ` · key ${destination.key_id}` : ''}
            </div>
          </div>
          <div className="workspace-field">
            <strong>Storage objects</strong>
            <div>
              {status?.object_backup?.enabled ? 'Included' : 'Not included'} ·{' '}
              {status?.object_backup?.bucket || '—'}
            </div>
          </div>
        </div>
        {destination.encryption_key_configured === false && (
          <Alert tone="warning" title="Backup is not operational">
            No backup encryption key is configured, so the worker cannot produce an artifact.
          </Alert>
        )}
        <p className="ops-muted">
          Last successful:{' '}
          {fmtStamp(status?.last_successful?.finished_at || status?.last_successful?.requested_at)}
          {' · '}Last failure: {fmtStamp(status?.last_failed?.finished_at)}
          {activeJob ? ` · In flight: ${activeJob.kind} (${activeJob.status})` : ''}
        </p>
      </Card>

      <Card title="Backup history" style={{ marginTop: 16 }}>
        <DataTable
          caption="Admin backup history (newest first, non-secret metadata)"
          columns={columns}
          rows={jobs}
          rowKey="id"
          emptyLabel="No backup has been requested yet."
        />
      </Card>

      {pair && (
        <Card
          title={`Backup set ${pair.backup_set_id}`}
          actions={
            <Button variant="ghost" size="sm" onClick={() => setPair(null)}>
              Close
            </Button>
          }
          style={{ marginTop: 16 }}
        >
          <Alert
            tone={pair.pair_complete ? 'success' : 'warning'}
            title={pair.pair_complete ? 'Consistent pair available' : 'Pair incomplete'}
          >
            {pair.pair_complete
              ? 'A completed database artifact and its completed object artifact both exist for this set.'
              : 'This set does not have both halves completed; a restore should not rely on it.'}
          </Alert>
          <div className="workspace-grid" style={{ marginTop: 12 }}>
            <div className="workspace-field">
              <strong>Database artifact</strong>
              <div>
                {pair.database
                  ? `${pair.database.status} · ${fmtBytes(pair.database.artifact_bytes)}`
                  : '—'}
              </div>
            </div>
            <div className="workspace-field">
              <strong>Object artifact</strong>
              <div>
                {pair.objects
                  ? `${pair.objects.status} · ${pair.objects.object_count ?? 0} objects · ${fmtBytes(pair.objects.object_bytes)}`
                  : '—'}
              </div>
            </div>
          </div>
        </Card>
      )}

      {form && (
        <Card title="Operational policy" style={{ marginTop: 16 }}>
          <p className="ops-muted">
            Only operational fields are configurable. Encryption, private storage,
            authorization, tenant isolation and integrity verification are enforced in code and
            have no switch to flip.
          </p>
          <div className="workspace-grid">
            <div className="workspace-field">
              <strong>Enabled</strong>
              <input
                type="checkbox"
                checked={!!form.enabled}
                onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
              />
            </div>
            <div className="workspace-field">
              <strong>Preferred frequency</strong>
              <select
                value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}
              >
                {FREQUENCIES.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>
            <div className="workspace-field">
              <strong>Retention (days)</strong>
              <input
                type="number"
                min="1"
                max="3650"
                value={form.retention_days}
                placeholder="no expiry"
                onChange={(e) => setForm({ ...form, retention_days: e.target.value })}
              />
            </div>
            <div className="workspace-field">
              <strong>Include storage objects</strong>
              <input
                type="checkbox"
                checked={!!form.object_backup_enabled}
                onChange={(e) => setForm({ ...form, object_backup_enabled: e.target.checked })}
              />
            </div>
            <div className="workspace-field">
              <strong>Object prefix</strong>
              <input
                type="text"
                value={form.object_prefix}
                onChange={(e) => setForm({ ...form, object_prefix: e.target.value })}
              />
            </div>
          </div>
          <div className="workspace-actions">
            <Button variant="primary" loading={busy === 'policy'} onClick={savePolicy}>
              Save policy
            </Button>
          </div>
          {policyMeta?.updated_at && (
            <p className="ops-muted">
              Last updated {fmtStamp(policyMeta.updated_at)}
              {policyMeta.updated_by ? ` by ${policyMeta.updated_by}` : ''}
            </p>
          )}
        </Card>
      )}

      {confirmCreate && (
        <ConfirmationDialog
          open
          title="Create a full backup?"
          message={
            'This queues a new backup of production data. It runs in the background and can be '
            + 'followed in the history below; storage objects are included when the stored '
            + 'policy enables them.'
          }
          confirmLabel="Create backup"
          busy={busy === 'create'}
          onClose={() => setConfirmCreate(false)}
          onConfirm={runCreate}
        />
      )}

    </div>
  );
}

