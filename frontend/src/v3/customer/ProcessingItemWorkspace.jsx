// frontend/src/v3/customer/ProcessingItemWorkspace.jsx
// CL-54 - genuine customer processing workspace. Uses ONLY the org-scoped
// /api/v3/processing/* surface (never the staff /api/v3/ops/* endpoints).
// Every write is server-authorized by the backend state machine; the UI never
// approves locally. Approve/Reject is the distinct owner/admin gate (D5).
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  calculateProcessingItem,
  confirmProcessingJob,
  getDocumentEmissions,
  getProcessingItemWorkspace,
  getProcessingJobs,
  getProcessingMappingOptions,
  resolveV3Membership,
  retryProcessingJob,
  reviewProcessingJob,
  saveProcessingExtraction,
  saveProcessingMapping,
  startProcessingItem,
  submitCustomerReview,
  validateProcessingItem,
} from '../api';
import WorkbenchShell from '../components/workbench/WorkbenchShell';
import EvidenceTrail from '../components/EvidenceTrail';
import {
  Alert,
  Button,
  ConfirmationDialog,
  ErrorState,
  LoadingState,
  SelectInput,
  StatusBadge,
  TextArea,
  TextInput,
} from '../components/ui';

const APPROVER_ROLES = ['owner', 'admin'];

const CUSTOMER_STAGES = [
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'validate', label: 'Validate' },
  { id: 'calculate', label: 'Calculate' },
  { id: 'review', label: 'Review' },
  { id: 'approve', label: 'Approve' },
  { id: 'evidence', label: 'Evidence' },
];

const STAGE_FOR_STATUS = {
  pending: 'extract',
  extracting: 'extract',
  extracted: 'extract',
  mapping: 'map',
  mapped: 'map',
  validating: 'validate',
  validated: 'validate',
  calculating: 'calculate',
  calculated: 'calculate',
  customer_review: 'review',
  approved: 'approve',
  rejected: 'approve',
  qc_approved: 'evidence',
  qc_rejected: 'evidence',
  completed: 'evidence',
  failed: 'extract',
};

// Statuses in which the extraction form may be edited/saved.
const EXTRACT_EDITABLE = ['pending', 'extracting', 'extracted'];
// Statuses from which mapping may be saved (extracted -> mapped, mapped rework).
const MAP_EDITABLE = ['extracted', 'mapping', 'mapped'];
// Statuses from which validation may be (re)run.
const VALIDATE_RUNNABLE = ['mapped', 'validating', 'validated'];
// Statuses from which calculation may be (re)run.
const CALCULATE_RUNNABLE = ['validated', 'calculating', 'calculated'];
// Statuses that may be sent to customer review.
const REVIEW_SENDABLE = ['calculated', 'customer_review'];
// Statuses on which an approver may decide (D5).
const DECIDABLE = ['calculated', 'customer_review'];

// Legacy demo data stored internal validation messages as field values; never
// surface them as user-facing content.
const DEBUG_PLACEHOLDER_RE = /^missing (extracted field|quantity|unit|.*value|.*field)/i;
const humanValue = (value) => {
  if (value == null) return '';
  const s = String(value);
  if (DEBUG_PLACEHOLDER_RE.test(s.trim())) return '';
  return s;
};

const EMPTY_LINE = { description: '', activity: '', quantity: '', unit: '', amount: '' };

function formFromData(data = {}, suggestions = {}) {
  const d = { ...(suggestions || {}), ...(data || {}) };
  return {
    supplier: humanValue(d.supplier),
    invoice_number: humanValue(d.invoice_number),
    invoice_date: humanValue(d.invoice_date || d.date),
    activity: humanValue(d.activity),
    quantity: humanValue(d.quantity),
    unit: humanValue(d.unit),
    amount: humanValue(d.amount),
    currency: humanValue(d.currency) || 'GBP',
  };
}

function linesFromData(data = {}) {
  const existing = (data || {}).line_items || [];
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
}

export default function ProcessingItemWorkspace({ itemId, onBack }) {
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [preset, setPreset] = useState('50-50');
  const [confirm, setConfirm] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [customerNotes, setCustomerNotes] = useState('');

  const [header, setHeader] = useState({});
  const [lines, setLines] = useState([{ ...EMPTY_LINE }]);
  const [mapping, setMapping] = useState({ factor_id: '', line_factors: [] });
  const [mappingOptions, setMappingOptions] = useState({ factors: [], no_factors_reason: '' });

  const [evidence, setEvidence] = useState(null);
  const [evidenceError, setEvidenceError] = useState('');
  const [job, setJob] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const membership = await resolveV3Membership();
      setRole(membership?.role || null);
      const w = await getProcessingItemWorkspace(itemId);
      setWorkspace(w);
      const data = w?.data || {};
      setHeader(formFromData(data.extracted_data, w?.source?.ocr_suggestions));
      setLines(linesFromData(data.extracted_data));
      const mapped = data.mapped_data || {};
      if (Array.isArray(mapped.line_items)) {
        setMapping({ factor_id: '', line_factors: mapped.line_items.map((m) => m.factor_id || '') });
      } else {
        setMapping({ factor_id: data.emission_factor_used || mapped.factor_id || '', line_factors: [] });
      }
      if (w?.batch?.organization_id) {
        try {
          const jobs = await getProcessingJobs(w.batch.organization_id, { limit: 500 });
          const mine = (jobs.jobs || []).find((j) => j.source_item_id === w.item.id);
          setJob(mine || null);
        } catch (_e) {
          setJob(null);
        }
      }
      if (w?.item?.file_id) {
        getDocumentEmissions(w.item.file_id)
          .then(setEvidence)
          .catch((e) => setEvidenceError(e.message || 'Evidence lookup unavailable'));
      }
    } catch (e) {
      setError(e.message || 'Failed to load the processing workspace');
    } finally {
      setLoading(false);
    }
  }, [itemId]);

  useEffect(() => {
    let active = true;
    load().finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemId, retryCount]);

  // Light status refresh while the item is still in flight.
  useEffect(() => {
    const status = workspace?.item?.status;
    const inFlight = status && !['approved', 'rejected', 'qc_approved', 'qc_rejected', 'completed', 'failed'].includes(status);
    if (!inFlight) return undefined;
    const timer = setInterval(() => {
      getProcessingItemWorkspace(itemId)
        .then((w) => setWorkspace(w))
        .catch(() => { /* keep last known state */ });
    }, 10000);
    return () => clearInterval(timer);
  }, [itemId, workspace?.item?.status]);

  const item = workspace?.item || {};
  const data = workspace?.data || {};
  const source = workspace?.source || {};
  const issues = workspace?.issues || [];
  const status = item.status || 'pending';
  const isApprover = APPROVER_ROLES.includes(role);

  const editableExtraction = EXTRACT_EDITABLE.includes(status);
  const editableMapping = MAP_EDITABLE.includes(status);
  const canValidate = VALIDATE_RUNNABLE.includes(status);
  const canCalculate = CALCULATE_RUNNABLE.includes(status);
  const canSendReview = REVIEW_SENDABLE.includes(status);
  const canDecide = isApprover && DECIDABLE.includes(status);

  const hasLines = (workspace?.data?.extracted_data || {}).line_items?.length > 0;
  const findings = (workspace?.validation && (workspace.validation.findings || [])) || [];
  const blockingFindings = findings.filter((f) => f.severity === 'error' || f.severity === 'critical');
  const factors = mappingOptions.factors || [];
  // CL-44 / D-cf-5 — approved customer factors join the picker and take
  // precedence over CarbonTally-managed factors for the same activity/unit.
  const customerFactors = mappingOptions.customer_factors || [];
  const allFactorOptions = [...customerFactors, ...factors];

  const factorLabel = (factor) => {
    const unit = factor.unit ? ` [${factor.unit}]` : '';
    const isCustomer =
      factor.factor_kind === 'customer_factor' ||
      String(factor.factor_source || '').toUpperCase() === 'CUSTOMER';
    const source = isCustomer
      ? `Customer factor v${factor.version || 1}`
      : `${factor.factor_source || ''} ${factor.reporting_year || ''}`.trim();
    return `${factor.activity_type || factor.id}${unit} · ${source}`.trim();
  };
  const spendSuggestion = mappingOptions.spend_suggestion || null;

  const buildExtractionPayload = () => {
    const hasLineRows = lines.some((l) => String(l.activity || '').trim() || String(l.quantity || '').trim());
    const payload = {
      supplier: header.supplier,
      invoice_number: header.invoice_number,
      date: header.invoice_date,
      currency: header.currency,
    };
    if (hasLineRows) {
      payload.line_items = lines
        .filter((l) => String(l.activity || '').trim() || String(l.quantity || '').trim())
        .map((l) => ({
          description: l.description,
          activity: l.activity,
          quantity: l.quantity === '' ? null : Number(l.quantity),
          unit: l.unit,
          amount: l.amount === '' ? null : Number(l.amount),
        }));
    } else {
      payload.activity = header.activity;
      payload.quantity = header.quantity === '' ? null : Number(header.quantity);
      payload.unit = header.unit;
      payload.amount = header.amount === '' ? null : Number(header.amount);
    }
    return payload;
  };

  const onSaveExtraction = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const payload = buildExtractionPayload();
      await startProcessingItem(itemId, 'extraction');
      const saved = await saveProcessingExtraction(itemId, payload);
      setWorkspace((prev) => ({ ...prev, item: saved, data: { ...prev?.data, extracted_data: payload } }));
      setNotice('Extraction saved. Ready to map factors.');
    } catch (e) {
      setError(e.message || 'Failed to save extraction');
    } finally {
      setBusy(false);
    }
  };

  const loadMappingOptions = async () => {
    setError('');
    try {
      const options = await getProcessingMappingOptions(itemId);
      setMappingOptions(options);
      setNotice('Mapping options loaded - select an emission factor below.');
    } catch (e) {
      setError(e.message || 'Failed to load mapping options');
    }
  };

  const onSaveMapping = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const payload = hasLines
        ? {
            mapped_data: {
              line_items: lines.map((l, i) => ({
                factor_id: mapping.line_factors[i] || null,
                activity_type: l.activity || null,
                unit: l.unit || null,
              })),
            },
          }
        : {
            mapped_data: { factor_id: mapping.factor_id || null },
            emission_factor_used: mapping.factor_id || null,
          };
      const saved = await saveProcessingMapping(itemId, payload);
      setWorkspace((prev) => ({ ...prev, item: saved }));
      setNotice('Mapping saved. Ready to validate.');
    } catch (e) {
      setError(e.message || 'Failed to save mapping');
    } finally {
      setBusy(false);
    }
  };

  const onValidate = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await validateProcessingItem(itemId);
      setWorkspace((prev) => ({ ...prev, item: result.item, validation: result }));
      if (result.blocking) {
        setNotice(`Validation found blocking issues (${result.findings?.length || 0}). Fix them, then validate again.`);
      } else {
        setNotice('Validation passed - ready to calculate.');
      }
    } catch (e) {
      setError(e.message || 'Validation failed');
    } finally {
      setBusy(false);
    }
  };

  // CL-2: the state machine requires validated -> calculating -> calculated, so
  // Calculate first claims the calculation stage, then runs the engine.
  const onCalculate = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await startProcessingItem(itemId, 'calculation');
      const result = await calculateProcessingItem(itemId, {});
      setWorkspace((prev) => ({
        ...prev,
        item: result.item,
        data: {
          ...prev?.data,
          calculated_emissions_kg_co2e: result.calculation?.co2e_kg ?? result.item?.calculated_emissions_kg_co2e,
        },
      }));
      setNotice('Calculated server-side. Review the result, then send to review.');
      if (item.file_id) {
        getDocumentEmissions(item.file_id).then(setEvidence).catch(() => {});
      }
    } catch (e) {
      setError(e.message || 'Calculation failed');
    } finally {
      setBusy(false);
    }
  };

  const onSendToReview = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await startProcessingItem(itemId, 'review');
      const w = await getProcessingItemWorkspace(itemId);
      setWorkspace(w);
      setNotice('Sent to customer review. An owner or administrator can now approve or reject it.');
    } catch (e) {
      setError(e.message || 'Failed to send to review');
    } finally {
      setBusy(false);
    }
  };

  const onDecide = async () => {
    if (!confirm) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const approved = confirm.tone === 'approve';
      await submitCustomerReview(itemId, {
        approved,
        rejection_reason: approved ? null : rejectionReason,
        customer_notes: customerNotes || null,
      });
      if (job && job.stage === 'review') {
        try {
          await reviewProcessingJob(job.id, {
            approved,
            rejection_reason: approved ? null : rejectionReason,
            customer_notes: customerNotes || null,
          });
        } catch (_e) { /* item decision is authoritative; job sync best-effort */ }
      }
      setConfirm(null);
      setRejectionReason('');
      setCustomerNotes('');
      const w = await getProcessingItemWorkspace(itemId);
      setWorkspace(w);
      setNotice(approved ? 'Item approved. The evidence chain is recorded.' : 'Item rejected. It has been returned for correction.');
    } catch (e) {
      setError(e.message || 'Failed to record your decision');
    } finally {
      setBusy(false);
    }
  };

  const onRetryJob = async () => {
    if (!job) return;
    setBusy(true);
    setError('');
    try {
      const updated = await retryProcessingJob(job.id);
      setJob(updated);
      setNotice('Automatic processing job re-enqueued.');
    } catch (e) {
      setError(e.message || 'Failed to retry the job');
    } finally {
      setBusy(false);
    }
  };

  const onConfirmJob = async (stage = 'enqueued', corrections = {}) => {
    if (!job) return;
    setBusy(true);
    setError('');
    try {
      const updated = await confirmProcessingJob(job.id, { stage, ...corrections });
      setJob(updated);
      setNotice('Automatic processing job confirmed - the worker will resume it.');
    } catch (e) {
      setError(e.message || 'Failed to confirm the job');
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <LoadingState label="Loading processing workspace..." />;
  if (error && !workspace) return <ErrorState inline message={error} onRetry={() => setRetryCount((n) => n + 1)} />;
  if (!workspace || !item.id) return <ErrorState inline message="Workspace unavailable." />;

  const extractionPane = (
    <div className="v3-inline-card" style={{ marginTop: 10 }}>
      <strong>Extraction</strong>
      {editableExtraction ? (
        <p className="v3-muted" style={{ margin: '4px 0 8px' }}>
          Confirm or correct the fields extracted from the source document. OCR suggestions are pre-filled for review.
        </p>
      ) : (
        <p className="v3-muted" style={{ margin: '4px 0 8px' }}>
          Extraction is locked once the item leaves the extraction stage.
        </p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <TextInput
          label="Supplier"
          value={header.supplier}
          disabled={!editableExtraction}
          onChange={(e) => setHeader({ ...header, supplier: e.target.value })}
        />
        <TextInput
          label="Invoice number"
          value={header.invoice_number}
          disabled={!editableExtraction}
          onChange={(e) => setHeader({ ...header, invoice_number: e.target.value })}
        />
        <TextInput
          label="Invoice date"
          value={header.invoice_date}
          disabled={!editableExtraction}
          onChange={(e) => setHeader({ ...header, invoice_date: e.target.value })}
        />
        <TextInput
          label="Currency"
          value={header.currency}
          disabled={!editableExtraction}
          onChange={(e) => setHeader({ ...header, currency: e.target.value })}
        />
      </div>

      {!hasLines ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
          <TextInput
            label="Activity"
            value={header.activity}
            disabled={!editableExtraction}
            onChange={(e) => setHeader({ ...header, activity: e.target.value })}
          />
          <TextInput
            label="Quantity"
            value={header.quantity}
            disabled={!editableExtraction}
            onChange={(e) => setHeader({ ...header, quantity: e.target.value })}
          />
          <TextInput
            label="Unit"
            value={header.unit}
            disabled={!editableExtraction}
            onChange={(e) => setHeader({ ...header, unit: e.target.value })}
          />
          <TextInput
            label="Amount"
            value={header.amount}
            disabled={!editableExtraction}
            onChange={(e) => setHeader({ ...header, amount: e.target.value })}
          />
        </div>
      ) : (
        <div style={{ marginTop: 8 }}>
          {lines.map((line, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, marginBottom: 6 }}>
              <TextInput
                label={i === 0 ? 'Description' : undefined}
                placeholder="Description"
                value={line.description}
                disabled={!editableExtraction}
                onChange={(e) => setLines((prev) => prev.map((l, j) => (j === i ? { ...l, description: e.target.value } : l)))}
              />
              <TextInput
                label={i === 0 ? 'Activity' : undefined}
                placeholder="Activity"
                value={line.activity}
                disabled={!editableExtraction}
                onChange={(e) => setLines((prev) => prev.map((l, j) => (j === i ? { ...l, activity: e.target.value } : l)))}
              />
              <TextInput
                label={i === 0 ? 'Qty' : undefined}
                placeholder="Quantity"
                value={line.quantity}
                disabled={!editableExtraction}
                onChange={(e) => setLines((prev) => prev.map((l, j) => (j === i ? { ...l, quantity: e.target.value } : l)))}
              />
              <TextInput
                label={i === 0 ? 'Unit' : undefined}
                placeholder="Unit"
                value={line.unit}
                disabled={!editableExtraction}
                onChange={(e) => setLines((prev) => prev.map((l, j) => (j === i ? { ...l, unit: e.target.value } : l)))}
              />
            </div>
          ))}
          {editableExtraction && (
            <Button variant="secondary" size="sm" icon="plus" onClick={() => setLines((prev) => [...prev, { ...EMPTY_LINE }])}>
              Add line
            </Button>
          )}
        </div>
      )}

      {editableExtraction && (
        <div style={{ marginTop: 10 }}>
          <Button variant="primary" onClick={onSaveExtraction} disabled={busy}>
            {busy ? 'Saving...' : 'Save extraction'}
          </Button>
        </div>
      )}
    </div>
  );
  const mappingPane = (
    <div className="v3-inline-card" style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <strong>Mapping</strong>
        <Button variant="secondary" size="sm" onClick={loadMappingOptions} disabled={busy}>
          Load factor options
        </Button>
      </div>
      {mappingOptions.no_factors_reason ? (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>{mappingOptions.no_factors_reason}</p>
      ) : null}
      {allFactorOptions.length === 0 ? (
        <div style={{ margin: '6px 0 0' }}>
          <p className="v3-muted">
            No factor options loaded yet. "Load factor options" suggests factors from the extracted activity and unit.
          </p>
          {spendSuggestion && (
            <div className="v3-inline-card" style={{ marginTop: 8, borderLeft: '3px solid var(--v3-warn, #b45309)' }}>
              <p className="v3-muted" style={{ margin: 0 }}>
                {spendSuggestion.message || `This is a spend-based activity (${spendSuggestion.unit || 'GBP'}). The current factor set is physical-unit based, so a customer factor is required.`}
              </p>
              <div style={{ marginTop: 8 }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigate('/organization?tab=factors')}
                >
                  Create a spend-based customer factor
                </Button>
              </div>
            </div>
          )}
        </div>
      ) : hasLines ? (
        lines.map((line, i) => (
          <div key={i} style={{ marginTop: 8 }}>
            <SelectInput
              label={`Factor - ${line.activity || `line ${i + 1}`}`}
              value={mapping.line_factors[i] || ''}
              disabled={!editableMapping}
              onChange={(e) =>
                setMapping((prev) => {
                  const next = [...(prev.line_factors || [])];
                  next[i] = e.target.value;
                  return { ...prev, line_factors: next };
                })
              }
            >
              <option value="">Select an emission factor...</option>
              {allFactorOptions.map((f) => (
                <option key={f.id} value={f.id}>{factorLabel(f)}</option>
              ))}
            </SelectInput>
          </div>
        ))
      ) : (
        <div style={{ marginTop: 8 }}>
          <SelectInput
            label="Emission factor"
            value={mapping.factor_id || ''}
            disabled={!editableMapping}
            onChange={(e) => setMapping((prev) => ({ ...prev, factor_id: e.target.value }))}
          >
            <option value="">Select an emission factor...</option>
            {allFactorOptions.map((f) => (
              <option key={f.id} value={f.id}>{factorLabel(f)}</option>
            ))}
          </SelectInput>
        </div>
      )}
      {editableMapping && (
        <div style={{ marginTop: 10 }}>
          <Button variant="primary" onClick={onSaveMapping} disabled={busy}>
            {busy ? 'Saving...' : 'Save mapping'}
          </Button>
        </div>
      )}
    </div>
  );

  const validationPane = (
    <div className="v3-inline-card" style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <strong>Validation</strong>
        {canValidate && (
          <Button variant="secondary" size="sm" onClick={onValidate} disabled={busy}>
            {busy ? 'Running...' : 'Run validation'}
          </Button>
        )}
      </div>
      {findings.length === 0 ? (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>
          No validation findings recorded yet.
        </p>
      ) : (
        <ul style={{ margin: '8px 0 0', paddingLeft: 18 }}>
          {findings.map((f, i) => (
            <li key={`${f.code}-${i}`} style={{ marginTop: 4 }}>
              <StatusBadge status={f.severity} />{' '}
              {f.field ? <code>{f.field}:</code> : null} {f.message || f.code}
            </li>
          ))}
        </ul>
      )}
      {blockingFindings.length > 0 && (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>
          Fix the blocking findings in Extraction/Mapping, then validate again.
        </p>
      )}
    </div>
  );

  const calculationPane = (
    <div className="v3-inline-card" style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <strong>Calculation</strong>
        {canCalculate && (
          <Button variant="secondary" size="sm" onClick={onCalculate} disabled={busy}>
            {busy ? 'Calculating...' : 'Calculate'}
          </Button>
        )}
      </div>
      {data.calculated_emissions_kg_co2e == null ? (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>
          No calculation yet. The server computes the result from the extracted quantity and mapped factor - the client never
          supplies it.
        </p>
      ) : (
        <div className="v3-result-card" style={{ marginTop: 8 }}>
          <strong>Calculated result</strong>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{data.calculated_emissions_kg_co2e} kg CO2e</div>
          <div className="v3-muted" style={{ fontSize: 12 }}>
            Scope {data.mapped_data?.scope || '-'} · Methodology {data.mapped_data?.methodology || 'direct_multiply'}
          </div>
        </div>
      )}
    </div>
  );
  const evidencePane = (
    <div className="v3-inline-card" style={{ marginTop: 10 }}>
      <strong>Emissions & evidence</strong>
      {evidenceError ? (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>{evidenceError}</p>
      ) : !evidence ? (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>
          Evidence appears here once this document has been calculated.
        </p>
      ) : (evidence.emissions || []).length === 0 ? (
        <p className="v3-muted" style={{ margin: '6px 0 0' }}>
          No emissions have been calculated from this document yet.
        </p>
      ) : (
        <div style={{ marginTop: 8 }}>
          {evidence.emissions.map((row) => (
            <div key={row.id} className="v3-inline-card" style={{ marginBottom: 8, padding: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                <strong>{row.activity || row.source_file || 'Emission'}</strong>
                <span>{row.calculated_kg_co2e} kg CO2e</span>
              </div>
              <div className="v3-muted" style={{ fontSize: 12, marginTop: 4 }}>
                {row.start_date || '-'} · Scope {row.scope || '-'} · Snapshot {row.snapshot_id || '-'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const jobBanner = job ? (
    <div className="v3-inline-card" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
        <div>
          <strong>Automatic processing</strong>
          <div className="v3-muted" style={{ fontSize: 12 }}>
            {job.stage_label} · attempt {job.attempt_count}/{job.max_attempts}
            {job.manual_review_reason ? ` · ${job.manual_review_reason}` : ''}
          </div>
        </div>
        <StatusBadge status={job.status} />
      </div>
      {(job.stage === 'blocked' || job.stage === 'failed') && (
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <Button variant="secondary" size="sm" onClick={() => onRetryJob()} disabled={busy}>
            Retry job
          </Button>
          {job.stage === 'blocked' && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onConfirmJob('enqueued', { extracted_data: workspace?.data?.extracted_data || undefined })}
              disabled={busy}
            >
              Confirm after review
            </Button>
          )}
        </div>
      )}
    </div>
  ) : null;

  const dataPane = (
    <>
      <div className="ct-pane__header">
        Structured data · <StatusBadge status={status} />
      </div>
      <div className="ct-pane__body">
        {jobBanner}
        {extractionPane}
        {mappingPane}
        {validationPane}
        {calculationPane}
        {evidencePane}
        {issues.length > 0 && (
          <div className="v3-inline-card" style={{ marginTop: 10 }}>
            <strong>Linked issues ({issues.length})</strong>
            {issues.map((issue) => (
              <div key={issue.id} style={{ marginTop: 4 }}>
                <StatusBadge status={issue.status} /> {issue.title || issue.issue_type}
              </div>
            ))}
          </div>
        )}
        <div className="v3-mono" style={{ marginTop: 12, whiteSpace: 'pre-wrap' }}>
          {JSON.stringify(workspace?.data || {}, null, 2)}
        </div>
      </div>
    </>
  );
  const actionsPane = (
    <div style={{ padding: '12px 0 0', border: 'none' }}>
      {!isApprover && status !== 'approved' && (
        <p className="ct-field__hint" style={{ marginTop: 0 }}>
          You can work this item through extraction, mapping, validation and calculation. Approving or rejecting is reserved for
          an organisation owner or administrator.
        </p>
      )}
      {canSendReview && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Button variant="primary" icon="send" onClick={onSendToReview} disabled={busy}>
            Send to review
          </Button>
        </div>
      )}
      {canDecide && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
          <Button variant="approve" icon="check" onClick={() => setConfirm({ tone: 'approve' })} disabled={busy}>
            Approve
          </Button>
          <Button variant="reject" icon="x" onClick={() => setConfirm({ tone: 'reject' })} disabled={busy}>
            Reject
          </Button>
        </div>
      )}
      {!canDecide && !canSendReview && (status === 'approved' || status === 'rejected') && (
        <p className="ct-field__hint" style={{ marginTop: 0 }}>
          This item has been decided ({status}). The decision is recorded server-side with reviewer identity and timestamp.
        </p>
      )}
      {canSendReview && (
        <div style={{ marginTop: 12 }}>
          <EvidenceTrail
            title="Evidence trail"
            steps={[
              { id: 'source', label: 'Source document', detail: item.file_name, tone: 'complete' },
              {
                id: 'extraction',
                label: 'Extraction',
                detail: humanValue(data.extracted_data?.activity) || 'recorded',
                tone: data.extracted_data?.activity ? 'complete' : 'partial',
              },
              {
                id: 'mapping',
                label: 'Mapping',
                detail: data.mapped_data?.activity_type || data.emission_factor_used || 'recorded',
                tone: data.mapped_data?.factor_id || data.emission_factor_used ? 'complete' : 'partial',
              },
              {
                id: 'validation',
                label: 'Validation',
                detail: blockingFindings.length === 0 ? 'passed' : `${blockingFindings.length} blocking finding(s)`,
                tone: blockingFindings.length === 0 ? 'complete' : 'partial',
              },
              {
                id: 'calculation',
                label: 'Calculation',
                detail: data.calculated_emissions_kg_co2e != null ? `${data.calculated_emissions_kg_co2e} kg CO2e` : '-',
                tone: data.calculated_emissions_kg_co2e != null ? 'complete' : 'partial',
              },
            ]}
          />
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <Button variant="secondary" icon="arrowLeft" onClick={onBack || (() => navigate('/processing'))}>
          Back to processing
        </Button>
        {item.id && (
          <Button variant="secondary" onClick={() => navigate(`/review/${item.id}`)}>
            Open review workbench
          </Button>
        )}
      </div>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div className="v3-page" style={{ paddingBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 20 }}>Processing workspace</h1>
            <p className="v3-subtitle" style={{ marginTop: 4 }}>{item.file_name || 'Unnamed item'}</p>
          </div>
          <StatusBadge status={status} />
        </div>
        {notice && <Alert tone="success" title="Done">{notice}</Alert>}
        {error && <Alert tone="error" title="Action not completed">{error}</Alert>}
      </div>

      <WorkbenchShell
        stages={CUSTOMER_STAGES}
        currentStage={STAGE_FOR_STATUS[status] || 'extract'}
        preset={preset}
        onPresetChange={setPreset}
        sourceUrl={source.viewer_url}
        sourceTitle={source.file_name}
        allowDownload={false}
        status={status}
        data={dataPane}
        dataLabel="Data & actions"
        actions={actionsPane}
      />

      {confirm && (
        <ConfirmationDialog
          open
          title={confirm.tone === 'approve' ? 'Approve this item?' : 'Reject this item?'}
          message={
            confirm.tone === 'approve'
              ? 'Approval records a customer decision on this calculated result. The decision is stored server-side with your identity and timestamp.'
              : 'Rejection returns the item for correction. A reason is required.'
          }
          confirmLabel={confirm.tone === 'approve' ? 'Approve' : 'Reject'}
          tone={confirm.tone}
          busy={busy}
          onClose={() => setConfirm(null)}
          onConfirm={onDecide}
        >
          {confirm.tone === 'reject' && (
            <label className="ct-field__label" htmlFor="rejection-reason">
              Rejection reason <span className="ct-field__required">*</span>
              <TextArea
                id="rejection-reason"
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Explain what needs correcting."
              />
            </label>
          )}
        </ConfirmationDialog>
      )}
    </div>
  );
}
