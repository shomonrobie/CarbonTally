// frontend/src/v3/ops/ExtractionPanel.jsx
// D23 — shared human extraction workspace used by the internal operator queue
// and the Processing Entity workspace. Provides:
//   * a document viewer (the item's file, side-by-side with the form)
//   * invoice header fields (supplier, invoice number, invoice date, billing
//     period, currency)
//   * multi-line extraction (description/activity/quantity/unit/amount rows —
//     never overwriting previous lines)
//   * per-line mapping via the real factor candidates (activity type + factor
//     picker — no UUID typing)
//   * save/resume (persisted extracted_data reloads into the form)
//   * next/previous item navigation inside the batch
import React, { useEffect, useMemo, useState } from 'react';
import './ops.css';

const EMPTY_LINE = { description: '', activity: '', quantity: '', unit: '', amount: '' };

function headerFromData(data = {}) {
  return {
    supplier: data.supplier || '',
    invoice_number: data.invoice_number || '',
    invoice_date: data.invoice_date || data.date || '',
    billing_period_start: data.billing_period_start || '',
    billing_period_end: data.billing_period_end || '',
    currency: data.currency || 'GBP',
  };
}

export default function ExtractionPanel({ item, items, api, onItemChange }) {
  const [header, setHeader] = useState(headerFromData(item?.extracted_data));
  const [lines, setLines] = useState(() => {
    const existing = (item?.extracted_data || {}).line_items || [];
    return existing.length ? existing.map((l) => ({ ...EMPTY_LINE, ...l })) : [{ ...EMPTY_LINE }];
  });
  const [mapping, setMapping] = useState(() => {
    const ml = (item?.mapped_data || {}).line_items || [];
    return ml.map((l) => ({ activity_type: l.activity_type || '', factor_id: l.factor_id || '' }));
  });
  const [factors, setFactors] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const itemId = item?.id;


  useEffect(() => {
    setHeader(headerFromData(item?.extracted_data));
    const existing = (item?.extracted_data || {}).line_items || [];
    setLines(existing.length ? existing.map((l) => ({ ...EMPTY_LINE, ...l })) : [{ ...EMPTY_LINE }]);
    const ml = (item?.mapped_data || {}).line_items || [];
    setMapping(ml.map((l) => ({ activity_type: l.activity_type || '', factor_id: l.factor_id || '' })));
    setError('');
    setNotice('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId]);

  const firstActivity = useMemo(() => {
    const found = lines.find((l) => l.activity && l.unit);
    return found ? { activity: found.activity, unit: found.unit } : null;
  }, [lines]);

  useEffect(() => {
    if (!itemId || !firstActivity) return;
    let active = true;
    setBusy(true);
    api
      .getMappingOptions(itemId, firstActivity)
      .then((body) => { if (active) setFactors(body.factors || []); })
      .catch(() => { if (active) setFactors([]); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId, firstActivity?.activity, firstActivity?.unit]);

  const run = async (action) => {
    if (!itemId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      if (action === 'start') {
        await api.startItem(itemId, 'extraction');
        setNotice('Stage claimed (extracting).');
      } else if (action === 'extract' || action === 'draft') {
        await api.extractItem(itemId, {
          ...header,
          date: header.invoice_date || undefined,
          line_items: lines,
        });
        setNotice(action === 'draft' ? 'Draft saved.' : 'Extraction saved.');
      } else if (action === 'map') {
        await api.mapItem(itemId, {
          mapped_data: {
            line_items: lines.map((_, i) => mapping[i] || { activity_type: '', factor_id: '' }),
          },
        });
        setNotice('Mapping saved.');
      } else if (action === 'calculate') {
        const res = await api.calculateItem(itemId, {});
        const co2e = res.result ? Number(res.result.co2e_kg) : null;
        setNotice(
          co2e != null
            ? `Calculation complete — ${co2e.toFixed(2)} kg CO₂e.`
            : 'Calculation complete.'
        );
      }
      if (onItemChange) await onItemChange(itemId);
    } catch (e) {
      setError(e.message || 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  const setLine = (idx, field, value) => {
    const next = lines.slice();
    next[idx] = { ...(next[idx] || EMPTY_LINE), [field]: value };
    setLines(next);
    if (field === 'activity' || field === 'unit') {
      setMapping((m) => {
        const n = m.slice();
        n[idx] = { activity_type: '', factor_id: '' };
        return n;
      });
    }
  };

  const addLine = () => setLines((l) => [...l, { ...EMPTY_LINE }]);
  const removeLine = (idx) => {
    setLines((l) => (l.length === 1 ? [{ ...EMPTY_LINE }] : l.filter((_, i) => i !== idx)));
    setMapping((m) => m.filter((_, i) => i !== idx));
  };

  const factorLabel = (f) =>
    `${f.activity_type} · ${f.unit || 'unit?'} · ${f.factor_source || ''} ${f.reporting_year || ''}`;

  const status = item?.status || 'pending';
  const index = items.findIndex((i) => i.id === itemId);
  const hasPrev = index > 0;
  const hasNext = items.length > 0 && index < items.length - 1;

  return (
    <div className="extraction-panel">
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}

      <div className="extraction-grid">
        <div className="extraction-doc">
          <h3>Document</h3>
          {item?.file_url ? (
            <iframe
              className="doc-viewer"
              src={item.file_url}
              title={item.file_name || 'Document'}
              sandbox="allow-same-origin"
            />
          ) : (
            <div className="v3-ops-card muted">No document attached.</div>
          )}
          <div className="muted">
            {item?.file_name || ''} · {item?.page_count || 1} page(s) · status {status}
          </div>
        </div>

        <div className="extraction-form">
          <h3>Extraction — {item?.file_name || itemId}</h3>

          <div className="extraction-header-grid">
            <label>Supplier
              <input value={header.supplier} onChange={(e) => setHeader({ ...header, supplier: e.target.value })} />
            </label>
            <label>Invoice number
              <input value={header.invoice_number} onChange={(e) => setHeader({ ...header, invoice_number: e.target.value })} />
            </label>
            <label>Invoice date
              <input type="date" value={header.invoice_date} onChange={(e) => setHeader({ ...header, invoice_date: e.target.value })} />
            </label>
            <label>Billing period start
              <input type="date" value={header.billing_period_start} onChange={(e) => setHeader({ ...header, billing_period_start: e.target.value })} />
            </label>
            <label>Billing period end
              <input type="date" value={header.billing_period_end} onChange={(e) => setHeader({ ...header, billing_period_end: e.target.value })} />
            </label>
            <label>Currency
              <input value={header.currency} onChange={(e) => setHeader({ ...header, currency: e.target.value })} />
            </label>
          </div>

          <h4>Line items</h4>
          <table className="line-table">
            <thead>
              <tr>
                <th>Description</th><th>Activity</th><th>Quantity</th><th>Unit</th>
                <th>Amount</th><th>Factor</th><th />
              </tr>
            </thead>
            <tbody>
              {lines.map((line, idx) => (
                <tr key={idx}>
                  <td><input value={line.description} onChange={(e) => setLine(idx, 'description', e.target.value)} /></td>
                  <td><input value={line.activity} placeholder="e.g. Natural gas" onChange={(e) => setLine(idx, 'activity', e.target.value)} /></td>
                  <td><input value={line.quantity} onChange={(e) => setLine(idx, 'quantity', e.target.value)} /></td>
                  <td><input value={line.unit} placeholder="kWh" onChange={(e) => setLine(idx, 'unit', e.target.value)} /></td>
                  <td><input value={line.amount} onChange={(e) => setLine(idx, 'amount', e.target.value)} /></td>
                  <td>
                    <select
                      value={mapping[idx]?.factor_id || ''}
                      onChange={(e) =>
                        setMapping((m) => {
                          const n = m.slice();
                          const f = factors.find((x) => x.id === e.target.value);
                          n[idx] = { activity_type: f?.activity_type || '', factor_id: e.target.value };
                          return n;
                        })
                      }
                    >
                      <option value="">— select factor —</option>
                      {factors.map((f) => (
                        <option key={f.id} value={f.id}>{factorLabel(f)}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <button className="v3-btn v3-btn-sm" onClick={() => removeLine(idx)}>×</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="workspace-actions">
            <button className="v3-btn" onClick={addLine}>+ Add line</button>
          </div>

          <div className="workspace-actions">
            {status === 'pending' && (
              <button className="v3-btn primary" disabled={busy} onClick={() => run('start')}>Claim stage</button>
            )}
            <button className="v3-btn primary" disabled={busy} onClick={() => run('extract')}>Save extraction</button>
            <button className="v3-btn" disabled={busy} onClick={() => run('draft')}>Save draft</button>
            <button className="v3-btn primary" disabled={busy || status === 'pending'} onClick={() => run('map')}>Save mapping</button>
            <button className="v3-btn primary" disabled={busy} onClick={() => run('calculate')}>Calculate</button>
          </div>

          <div className="workspace-actions">
            <button className="v3-btn" disabled={busy || !hasPrev} onClick={() => onItemChange(items[index - 1].id)}>← Previous item</button>
            <button className="v3-btn" disabled={busy || !hasNext} onClick={() => onItemChange(items[index + 1].id)}>Next item →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

