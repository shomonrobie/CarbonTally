// frontend/src/v3/customer/EmissionsPage.jsx
// Emissions & calculations — the authoritative V3 chain. The calculate form posts
// to /api/v3/emissions/calculate (the backend matches factors and computes the
// result; the frontend never calculates). History reads the persisted rows via
// the verified /api/v3/exports/emissions.json surface.
import React, { useCallback, useEffect, useState } from 'react';
import { getEmissionEvidence, resolveV3Organization, v3CalculateEmissions, v3ListEmissions } from '../api';
import EvidenceRecordPanel from '../components/EvidenceRecordPanel';
import { ErrorState } from '../components/StateViews';

const EMPTY_FORM = {
  activity: '',
  quantity: '',
  quantity_unit: 'kg',
  date: new Date().toISOString().slice(0, 10),
  reporting_year: new Date().getFullYear(),
  country: 'GB',
  scope: 'Scope 1',
  activity_type: '',
  facility_id: '',
  asset_id: '',
};

export default function EmissionsPage() {
  const [org, setOrg] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [evidence, setEvidence] = useState(null);
  const [evidenceError, setEvidenceError] = useState('');

  const openEvidence = (row) => {
    setEvidence(null);
    setEvidenceError('');
    getEmissionEvidence(row.id)
      .then(setEvidence)
      .catch((e) => setEvidenceError(e.message || 'Evidence unavailable'));
  };

  const loadHistory = useCallback(async (organizationId) => {
    try {
      const response = await v3ListEmissions(organizationId);
      setHistory(response.emissions || []);
    } catch (_e) {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const organization = await resolveV3Organization();
        if (!organization) {
          setError('No organization is linked to this account.');
          return;
        }
        setOrg(organization);
        await loadHistory(organization.id);
      } catch (e) {
        setError(e.message || 'Failed to load emissions');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [loadHistory, retryCount]);

  const onChange = (key) => (e) => {
    setForm({ ...form, [key]: e.target.value });
  };

  const onSubmit = async () => {
    setSubmitting(true);
    setError('');
    setNotice('');
    setResult(null);
    try {
      const payload = {
        organization_id: org.id,
        activity: form.activity,
        quantity: String(form.quantity),
        quantity_unit: form.quantity_unit,
        date: form.date,
        reporting_year: Number(form.reporting_year),
        country: form.country,
        scope: form.scope,
      };
      if (form.activity_type.trim()) payload.activity_type = form.activity_type.trim();
      if (form.facility_id.trim()) payload.facility_id = form.facility_id.trim();
      if (form.asset_id.trim()) payload.asset_id = form.asset_id.trim();
      const r = await v3CalculateEmissions(payload);
      setResult(r);
      setNotice('Calculation recorded.');
      await loadHistory(org.id);
    } catch (e) {
      setError(e.message || 'Calculation failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="v3-loading"><div className="spinner" />Loading emissions…</div>;
  if (error && !org) return <ErrorState message={error} onRetry={() => setRetryCount((n) => n + 1)} />;

  return (
    <div className="v3-page">
      <div className="v3-page-header">
        <h1>Emissions &amp; calculations</h1>
        <p className="v3-subtitle">
          Authoritative V3 calculation — the backend matches factors and computes results.
        </p>
      </div>

      {error && <div className="v3-error" style={{ marginBottom: 14 }}>{error}</div>}
      {notice && <div className="v3-note">{notice}</div>}

      <div className="v3-grid-2">
        <div className="v3-card">
          <h2>Calculate emissions</h2>
          <div className="v3-form-grid">
            <div className="v3-form-group">
              <label>Activity</label>
              <input value={form.activity} onChange={onChange('activity')} placeholder="e.g. Diesel, Electricity, Flight (Short Haul)" />
            </div>
            <div className="v3-form-group">
              <label>Quantity</label>
              <input type="number" min="0" value={form.quantity} onChange={onChange('quantity')} placeholder="1000" />
            </div>
            <div className="v3-form-group">
              <label>Unit</label>
              <select value={form.quantity_unit} onChange={onChange('quantity_unit')}>
                {['kg', 'L', 'kWh', 'm3', 'km', 't', 'units'].map((u) => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <div className="v3-form-group">
              <label>Date</label>
              <input type="date" value={form.date} onChange={onChange('date')} />
            </div>
            <div className="v3-form-group">
              <label>Reporting year</label>
              <input type="number" value={form.reporting_year} onChange={onChange('reporting_year')} />
            </div>
            <div className="v3-form-group">
              <label>Country</label>
              <select value={form.country} onChange={onChange('country')}>
                {['GB', 'IE', 'US', 'DE', 'FR'].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="v3-form-group">
              <label>Scope</label>
              <select value={form.scope} onChange={onChange('scope')}>
                <option value="Scope 1">Scope 1</option>
                <option value="Scope 2">Scope 2</option>
                <option value="Scope 3">Scope 3</option>
              </select>
            </div>
            <div className="v3-form-group">
              <label>Activity type (optional)</label>
              <input value={form.activity_type} onChange={onChange('activity_type')} placeholder="Standardized Fuel / Utility / Scope3" />
            </div>
          </div>
          <div className="v3-actions">
            <button
              className="v3-btn v3-btn-primary"
              onClick={onSubmit}
              disabled={submitting || !form.activity.trim() || !form.quantity}
            >
              {submitting ? 'Calculating…' : 'Calculate'}
            </button>
          </div>

          {result && (
            <div className="v3-result-card">
              <h3>Result</h3>
              <div className="v3-meta-list">
                <div className="v3-meta-item"><div className="k">kg CO₂e</div><div className="v">{result.co2e_kg ?? result.calculated_kg_co2e ?? '—'}</div></div>
                <div className="v3-meta-item"><div className="k">Scope</div><div className="v">{result.scope || '—'}</div></div>
                <div className="v3-meta-item"><div className="k">Snapshot id</div><div className="v">{result.snapshot_id || result.id || '—'}</div></div>
                <div className="v3-meta-item"><div className="k">Content hash</div><div className="v">{result.content_hash || '—'}</div></div>
                <div className="v3-meta-item"><div className="k">Factor</div><div className="v">{result.factor_source || result.factor_id || '—'}</div></div>
              </div>
            </div>
          )}
        </div>

          <div className="v3-card">
            <h2>Calculation history ({history.length})</h2>
            {history.length === 0 ? (
              <div className="v3-empty">No recorded calculations yet.</div>
            ) : (
              <>
                <table className="v3-table">
                  <thead>
                    <tr><th>Date</th><th>Activity</th><th>Scope</th><th>kg CO₂e</th><th>Factor</th><th></th></tr>
                  </thead>
                  <tbody>
                    {history.slice(0, 25).map((row) => (
                      <tr key={row.id}>
                        <td>{row.start_date || row.date || '—'}</td>
                        <td>{row.activity || row.activity_type || '—'}</td>
                        <td>{row.scope || '—'}</td>
                        <td>{row.calculated_kg_co2e ?? row.co2e_kg ?? '—'}</td>
                        <td className="v3-muted">{row.factor_source || row.factor_id || '—'}</td>
                        <td>
                          <button className="v3-btn v3-btn-sm" onClick={() => openEvidence(row)}>
                            View evidence
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {evidenceError && (
                  <div className="v3-muted" style={{ marginTop: 12 }}>{evidenceError}</div>
                )}

                {evidence && <EvidenceRecordPanel evidence={evidence} />}
              </>
            )}
          </div>
        </div>
      </div>
  );
}

