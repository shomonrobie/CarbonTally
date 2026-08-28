// frontend/src/v3/ops/ExtractionPanel.jsx
// D23/D19 — shared human extraction workspace used by the internal operator
// queue and the Processing Entity workspace. Rendered inside the D19
// WorkbenchShell (top workflow nav + split panes + pane presets + secure
// view-only source + status/autosave indicators). Provides:
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
import WorkbenchShell from '../components/workbench/WorkbenchShell';
import { Button, Icon } from '../components/ui';
import './ops.css';

const EMPTY_LINE = { description: '', activity: '', quantity: '', unit: '', amount: '' };

// CL-37 / UH-4 — legacy demo data stored internal validation messages as field
// values (e.g. "missing extracted field 'supplier'", "missing quantity"). These
// must never render as user-facing field content: treat them as empty so the
// operator sees the muted "no value extracted" hint instead of debug prose.
const DEBUG_PLACEHOLDER_RE = /^missing (extracted field|quantity|unit|.*value|.*field)/i;
const humanValue = (value) => {
  if (value == null) return '';
  const s = String(value);
  if (DEBUG_PLACEHOLDER_RE.test(s.trim())) return '';
  return s;
};

// D19 — default workflow stages for a Processing Entity extraction workspace.
const PE_STAGES = [
  { id: 'queue', label: 'Queue' },
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'calculate', label: 'Calculate' },
  { id: 'clarify', label: 'Clarify' },
];

const STAFF_STAGES = [
  { id: 'queue', label: 'Queue' },
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'validate', label: 'Validate' },
  { id: 'review', label: 'Review' },
  { id: 'qc', label: 'QC' },
  { id: 'evidence', label: 'Evidence' },
];

function stageForStatus(status, stages) {
  const map = {
    extracting: 'extract',
    extracted: 'extract',
    mapping: 'map',
    mapped: 'map',
    validating: 'validate',
    validated: 'validate',
    calculating: 'calculate',
    calculated: 'calculate',
    customer_review: 'review',
    qc_approved: 'qc',
    qc_rejected: 'qc',
    approved: 'review',
    rejected: 'review',
  };
  const fallback = stages.some((s) => s.id === 'extract') ? 'extract' : 'queue';
  return map[status] || fallback;
}

function headerFromData(data) {
  const d = data || {};
  return {
    supplier: humanValue(d.supplier),
    invoice_number: humanValue(d.invoice_number),
    invoice_date: humanValue(d.invoice_date || d.date),
    billing_period_start: humanValue(d.billing_period_start),
    billing_period_end: humanValue(d.billing_period_end),
    currency: humanValue(d.currency) || 'GBP',
  };
}

export default function ExtractionPanel({
  item,
  items,
  api,
  onItemChange,
  mode = 'pe',
  allowDownload = false,
  suggestions,
  validation,
}) {
  const [header, setHeader] = useState(headerFromData(item?.extracted_data) || {});
  const [lines, setLines] = useState(() => {
    const existing = (item?.extracted_data || {}).line_items || [];
    return existing.length
      ? existing.map((l) => ({
          ...EMPTY_LINE,
          description: humanValue(l.description),
          activity: humanValue(l.activity),
          quantity: humanValue(l.quantity),
          unit: humanValue(l.unit),
          amount: humanValue(l.amount),
        }))
      : [{ ...EMPTY_LINE }];
  });
  const [mapping, setMapping] = useState(() => {
    const ml = (item?.mapped_data || {}).line_items || [];
    return ml.map((l) => ({ activity_type: l.activity_type || '', factor_id: l.factor_id || '' }));
  });
  const [factors, setFactors] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [preset, setPreset] = useState('50-50');

  const itemId = item?.id;
  const stages = mode === 'staff' ? STAFF_STAGES : PE_STAGES;

  // D19 — lock state is DERIVED from the server item status. Once the item has
  // left the editable stages, the workbench is read-only. The frontend never
  // changes workflow state on its own.
  const LOCKED_STATUSES = [
    'validating', 'validated', 'calculating', 'calculated', 'customer_review',
    'approved', 'rejected', 'qc_approved', 'qc_rejected', 'completed', 'failed',
  ];
  const locked = LOCKED_STATUSES.includes(item?.status);

  // D19 — server validation findings mapped onto structured fields.
  const findings = Array.isArray(validation)
    ? validation
    : (validation && Array.isArray(validation.findings) ? validation.findings : []);
  const blockingFindings = findings.filter((f) => f.severity === 'error' || f.severity === 'critical');
  const fieldErrors = {};
  findings.forEach((f) => {
    if (!f.field) return;
    const key = String(f.field);
    if (!fieldErrors[key]) fieldErrors[key] = [];
    fieldErrors[key].push(f.message || f.code || 'Validation failed');
  });
  const errorFor = (key) => (fieldErrors[key] || []).join('; ');

  // D19 — source↔field affordance: which fields were auto-suggested from the
  // source OCR text (deterministic suggestions, always needing confirmation).
  // Confidence is only shown when a real numeric value is present.
  const suggestedKeys = suggestions ? Object.keys(suggestions) : [];

  const suggestedFor = (key, value) => {
    if (!suggestions) return null;
    if (key === 'quantity') {
      return value != null && String(value) === String(suggestions.quantity) ? 'Suggested' : null;
    }
    if (key === 'unit') {
      return value != null && String(value) === String(suggestions.unit) ? 'Suggested' : null;
    }
    return suggestedKeys.includes(key) ? 'Suggested' : null;
  };

  const SuggestionChip = ({ field, value, label }) => {
    const tag = suggestedFor(field, value);
    if (!tag) return null;
    return (
      <span className="ct-suggestion" title={`Auto-suggested from the source document (${label}) — confirm before saving.`}>
        <Icon name="zap" size={11} aria-hidden="true" /> {tag}
      </span>
    );
  };

  const FieldError = ({ field }) => {
    const message = errorFor(field);
    if (!message) return null;
    return <p className="ct-field__error" role="alert" id={`field-${field}-error`}>{message}</p>;
  };

  useEffect(() => {
    setHeader(headerFromData(item?.extracted_data) || {});
    const existing = (item?.extracted_data || {}).line_items || [];
    setLines(
      existing.length
        ? existing.map((l) => ({
            ...EMPTY_LINE,
            description: humanValue(l.description),
            activity: humanValue(l.activity),
            quantity: humanValue(l.quantity),
            unit: humanValue(l.unit),
            amount: humanValue(l.amount),
          }))
        : [{ ...EMPTY_LINE }]
    );
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
        // CL-2/PRC-1 — the backend state machine requires
        // `validated -> calculating -> calculated`. The UI must claim the
        // intermediate `calculation` stage before invoking the authoritative
        // engine, or the engine correctly returns 409.
        if (status !== 'calculating' && status !== 'calculated') {
          await api.startItem(itemId, 'calculation');
        }
        const res = await api.calculateItem(itemId, {});
        const co2e = res.result ? Number(res.result.co2e_kg) : (res.calculation ? Number(res.calculation.co2e_kg) : null);
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
  const autosaveState = busy ? 'saving' : notice ? 'saved' : error ? 'error' : 'idle';

  const dataPane = (
    <div className="extraction-form">
      {error && <div className="v3-ops-error">{error}</div>}
      {notice && <div className="v3-ops-notice">{notice}</div>}
      {blockingFindings.length > 0 && (
        <div className="v3-ops-error" role="alert">
          <strong>Validation ({blockingFindings.length})</strong> — resolve the flagged fields before calculation.
        </div>
      )}
      {locked && (
        <div className="v3-ops-notice">
          <strong>Locked</strong> — this item is in “{item?.status}” and is read-only in the workbench.
        </div>
      )}
      <h3>Extraction — {item?.file_name || itemId}</h3>

      <div className="extraction-header-grid">
        <label>Supplier <SuggestionChip field="supplier" value={header.supplier} label="supplier" />
          <input value={header.supplier} onChange={(e) => setHeader({ ...header, supplier: e.target.value })} aria-invalid={errorFor('supplier') ? 'true' : undefined} aria-describedby={errorFor('supplier') ? 'field-supplier-error' : undefined} disabled={locked} />
          <FieldError field="supplier" />
        </label>
        <label>Invoice number <SuggestionChip field="invoice_number" value={header.invoice_number} label="invoice number" />
          <input value={header.invoice_number} onChange={(e) => setHeader({ ...header, invoice_number: e.target.value })} aria-invalid={errorFor('invoice_number') ? 'true' : undefined} aria-describedby={errorFor('invoice_number') ? 'field-invoice_number-error' : undefined} disabled={locked} />
          <FieldError field="invoice_number" />
        </label>
        <label>Invoice date <SuggestionChip field="date" value={header.invoice_date} label="date" />
          <input type="date" value={header.invoice_date} onChange={(e) => setHeader({ ...header, invoice_date: e.target.value })} disabled={locked} />
          <FieldError field="date" />
        </label>
        <label>Billing period start
          <input type="date" value={header.billing_period_start} onChange={(e) => setHeader({ ...header, billing_period_start: e.target.value })} disabled={locked} />
        </label>
        <label>Billing period end
          <input type="date" value={header.billing_period_end} onChange={(e) => setHeader({ ...header, billing_period_end: e.target.value })} disabled={locked} />
        </label>
        <label>Currency
          <input value={header.currency} onChange={(e) => setHeader({ ...header, currency: e.target.value })} disabled={locked} />
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
              <td>
                <input value={line.description} onChange={(e) => setLine(idx, 'description', e.target.value)} disabled={locked} />
              </td>
              <td>
                <input value={line.activity} placeholder="e.g. Natural gas" onChange={(e) => setLine(idx, 'activity', e.target.value)} aria-invalid={errorFor('activity') ? 'true' : undefined} disabled={locked} />
                <SuggestionChip field="activity" value={line.activity} label="activity" />
                <FieldError field="activity" />
              </td>
              <td>
                <input value={line.quantity} onChange={(e) => setLine(idx, 'quantity', e.target.value)} aria-invalid={errorFor('quantity') ? 'true' : undefined} aria-describedby={errorFor('quantity') ? 'field-quantity-error' : undefined} disabled={locked} />
                <SuggestionChip field="quantity" value={line.quantity} label="quantity" />
                <FieldError field="quantity" />
              </td>
              <td>
                <input value={line.unit} placeholder="kWh" onChange={(e) => setLine(idx, 'unit', e.target.value)} aria-invalid={errorFor('unit') ? 'true' : undefined} aria-describedby={errorFor('unit') ? 'field-unit-error' : undefined} disabled={locked} />
                <SuggestionChip field="unit" value={line.unit} label="unit" />
                <FieldError field="unit" />
              </td>
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
        <Button variant="secondary" size="sm" icon="plus" onClick={addLine}>Add line</Button>
      </div>
    </div>
  );

  const actionBar = (
    <>
      {status === 'pending' && (
        <Button variant="primary" icon="zap" loading={busy} onClick={() => run('start')}>Claim stage</Button>
      )}
      <Button variant="approve" icon="save" loading={busy} disabled={locked} onClick={() => run('extract')}>Save extraction</Button>
      <Button variant="secondary" icon="save" loading={busy} disabled={locked} onClick={() => run('draft')}>Save draft</Button>
      <Button variant="primary" icon="link" loading={busy} disabled={locked || status === 'pending'} onClick={() => run('map')}>Save mapping</Button>
      <Button variant="primary" icon="calculator" loading={busy} disabled={locked} onClick={() => run('calculate')}>Calculate</Button>
      <span style={{ flex: 1 }} />
      <Button variant="secondary" icon="arrowLeft" loading={busy} disabled={!hasPrev} onClick={() => onItemChange(items[index - 1].id)}>Previous</Button>
      <Button variant="secondary" icon="arrowRight" loading={busy} disabled={!hasNext} onClick={() => onItemChange(items[index + 1].id)}>Next</Button>
    </>
  );

  return (
    <div className="extraction-panel">
      <WorkbenchShell
        stages={stages}
        currentStage={stageForStatus(status, stages)}
        preset={preset}
        onPresetChange={setPreset}
        sourceUrl={item?.file_url}
        sourceTitle={item?.file_name}
        allowDownload={allowDownload}
        status={status}
        locked={locked}
        autosaveState={autosaveState}
        data={dataPane}
        dataLabel="Extraction"
        actions={actionBar}
      />
    </div>
  );
}


