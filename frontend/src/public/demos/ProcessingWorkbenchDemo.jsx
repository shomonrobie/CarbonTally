// frontend/src/public/demos/ProcessingWorkbenchDemo.jsx
// The CarbonTally processing workbench (frozen D19 design).
//
// Demonstrates the split-screen workbench contract that every source +
// structured-data workflow uses across CarbonTally staff, Processing Entity
// staff and (in review mode) customers:
//   - TOP WORKFLOW NAVIGATION only (Queue → Extract → Map → Validate →
//     Review → QC → Evidence) — no left application sidebar inside the
//     workbench.
//   - Left pane: source document (secure, view-only, page controls, zoom,
//     NO download — the Processing Entity boundary).
//   - Right pane: structured data (fields, confidence, validation,
//     source↔field links, autosave, factor selection, review/QC, evidence).
//   - Pane presets 40/60 · 50/50 · 60/40.
//   - Mobile/tablet: the panes become a tray (Source ⇄ Data), never a
//     squeezed split (D20).
//
// Everything is local, deterministic, fabricated data.
import React, { useEffect, useRef, useState } from 'react';
import { DemoFrame, usePrefersReducedMotion } from './demoCore';
import { WORK_ITEM_DIESEL, EVIDENCE_CHAIN } from './demoData';
import './workbench.css';

// The frozen top workflow navigation (D19).
const STAGES = [
  { id: 'queue', label: 'Queue' },
  { id: 'extract', label: 'Extract' },
  { id: 'map', label: 'Map' },
  { id: 'validate', label: 'Validate' },
  { id: 'review', label: 'Review' },
  { id: 'qc', label: 'QC' },
  { id: 'evidence', label: 'Evidence' },
];

const PRESETS = [
  { id: '40/60', source: 40 },
  { id: '50/50', source: 50 },
  { id: '60/40', source: 60 },
];

const VALIDATION_CHECKS = [
  { label: 'Quantity present and numeric', ok: true },
  { label: 'Unit recognised (litres)', ok: true },
  { label: 'Activity mapped to an approved factor', ok: true },
  { label: 'Reporting year inferred from document', ok: true },
  { label: 'Unit consistent across source & data', ok: false },
  { label: 'Supplier verified against organisation records', ok: true },
];

const REVIEW_CHECKS = [
  { label: 'Extracted fields match the source document', ok: true },
  { label: 'Emission factor is the correct match for the activity', ok: true },
  { label: 'Calculation re-runs to the same snapshot', ok: true },
  { label: 'Evidence chain is complete', ok: true },
];

const QC_CHECKS = [
  { label: 'Headers confirmed', ok: true },
  { label: 'Line items confirmed', ok: true },
  { label: 'Factor provenance recorded', ok: true },
  { label: 'Calculation snapshot recorded', ok: true },
  { label: 'Evidence completeness recorded', ok: true },
];

const ITEM = WORK_ITEM_DIESEL;

export default function ProcessingWorkbenchDemo() {
  const reduced = usePrefersReducedMotion();
  const [stage, setStage] = useState(0);
  const [preset, setPreset] = useState('50/50');
  const [mobileTray, setMobileTray] = useState('source'); // D20 tray (mobile)
  const [linkedField, setLinkedField] = useState(null); // source↔field link demo
  const [saved, setSaved] = useState(false);
  const [guided, setGuided] = useState(false);
  const [approved, setApproved] = useState(false);
  const [qcPassed, setQcPassed] = useState(false);
  const panelRef = useRef(null);

  const item = ITEM;
  const current = STAGES[stage];
  const widths = PRESETS.find((p) => p.id === preset) || PRESETS[1];

  // Guided run: auto-advance through the stages (respects reduced motion).
  useEffect(() => {
    if (!guided) return undefined;
    if (reduced) {
      setStage(STAGES.length - 1);
      setGuided(false);
      return undefined;
    }
    if (stage >= STAGES.length - 1) {
      setGuided(false);
      return undefined;
    }
    const t = setTimeout(() => setStage((s) => s + 1), 1700);
    return () => clearTimeout(t);
  }, [guided, stage, reduced]);

  // Focus the workbench panel when the stage changes (keyboard use).
  useEffect(() => {
    if (panelRef.current) panelRef.current.focus();
  }, [stage]);

  const goStage = (i) => {
    setStage(Math.max(0, Math.min(STAGES.length - 1, i)));
    setLinkedField(null);
  };

  const linkField = (label) => setLinkedField((prev) => (prev === label ? null : label));
  const doSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 1600);
  };

  const markApproved = () => {
    setApproved(true);
    goStage(STAGES.findIndex((s) => s.id === 'evidence'));
  };
  const markQc = () => {
    setQcPassed(true);
    goStage(STAGES.findIndex((s) => s.id === 'evidence'));
  };

  return (
    <DemoFrame
      className="wb-frame"
      title="The CarbonTally processing workbench — split-screen, top workflow navigation"
      note="Interactive demonstration — fabricated invoice data, processed locally in the browser."
    >
      <div className="wb-app">
        {/* Top workflow navigation (D19): no left sidebar in this workbench. */}
        <div className="wb-workflow-nav" role="tablist" aria-label="Processing workflow stages">
          {STAGES.map((s, i) => (
            <button
              key={s.id}
              type="button"
              role="tab"
              aria-selected={i === stage}
              aria-controls="wb-panel"
              className={i === stage ? 'is-active' : i < stage ? 'is-done' : ''}
              onClick={() => goStage(i)}
            >
              <span className="wb-nav-dot" aria-hidden="true">
                {i < stage ? '✓' : i + 1}
              </span>
              <span className="wb-nav-label">{s.label}</span>
            </button>
          ))}
        </div>

        {/* Item context bar */}
        <div className="wb-context">
          <span className="wb-context-item">
            {item.batch} · {item.title}
          </span>
          <span className="wb-context-meta">
            {item.items} items · {item.assigned}
          </span>
          <span className={`wb-badge wb-badge-${current.id === 'review' || current.id === 'qc' ? 'warn' : 'neutral'}`}>
            {current.id === 'queue' ? 'Ready to process' : current.label}
          </span>
        </div>

        <div className="wb-body" id="wb-panel" ref={panelRef} tabIndex={-1}>
          {/* ---- SOURCE DOCUMENT pane (secure, view-only) ---- */}
          <section
            className={`wb-pane wb-source${mobileTray === 'source' ? ' is-active' : ''}`}
            style={{ flexBasis: `${widths.source}%` }}
            aria-label="Source document"
          >
            <div className="wb-pane-head">
              <span className="wb-kicker">Source document</span>
              <span className="wb-viewonly" title="View-only — no download for processing entities">
                <span aria-hidden="true">🔒</span> View only · no download
              </span>
            </div>
            <div className="wb-doc-toolbar">
              <span className="wb-doc-name">INV-2026-0417 · PDF (scanned)</span>
              <span className="wb-doc-controls">
                <span className="wb-doc-page">Page 1 / 3</span>
                <button type="button" aria-label="Zoom out">−</button>
                <button type="button" aria-label="Zoom in">+</button>
                <button type="button" aria-label="Fit to width">⤢</button>
              </span>
            </div>
            <div className="wb-doc-page">
              <div className="wb-invoice">
                <div className="wb-invoice-top">
                  <span className="wb-invoice-logo">MF</span>
                  <span className="wb-invoice-supplier">Meridian Fuel Supplies Ltd</span>
                </div>
                <div className="wb-invoice-line">Invoice {item.doc.ref}</div>
                <div className="wb-invoice-line">Date · {item.doc.date}</div>
                <div className="wb-invoice-line">Deliver to · {item.doc.site}</div>
                <div className="wb-invoice-items">
                  <span className="wb-invoice-item-head">Item</span>
                  <span className="wb-invoice-item-head">Qty</span>
                  <span className="wb-invoice-item-head">Amount</span>
                  <span className="wb-invoice-item">Red diesel</span>
                  <span className="wb-invoice-item">4,258.9 L</span>
                  <span className="wb-invoice-item">£9,845.20</span>
                </div>
                <div className="wb-invoice-note">Delivery note 3021</div>
                {linkedField ? (
                  <div className="wb-source-highlight" aria-live="polite">
                    <span className="wb-source-highlight-dot" aria-hidden="true" />
                    Linked to: <strong>{linkedField}</strong>
                  </div>
                ) : null}
              </div>
              {current.id === 'extract' ? (
                <div className="wb-scanline" aria-hidden="true" />
              ) : null}
            </div>
            <p className="wb-pane-foot">
              Stored in private, organisation-scoped storage. Processed through the
              portal — external processing entities cannot download customer documents.
            </p>
          </section>

          {/* ---- STRUCTURED DATA pane ---- */}
          <section
            className={`wb-pane wb-data${mobileTray === 'data' ? ' is-active' : ''}`}
            style={{ flexBasis: `${100 - widths.source}%` }}
            aria-label="Structured data"
          >
            <div className="wb-pane-head">
              <span className="wb-kicker">Structured data</span>
              <span className={`wb-save ${saved ? 'is-saved' : ''}`} aria-live="polite">
                {saved ? 'Saved ✓' : 'Autosave on'}
              </span>
            </div>

            {current.id === 'queue' && <QueueStage onClaim={() => goStage(1)} />}
            {current.id === 'extract' && (
              <ExtractStage
                linkedField={linkedField}
                onLink={linkField}
                onSave={doSave}
                onNext={() => goStage(2)}
              />
            )}
            {current.id === 'map' && (
              <MapStage onSave={doSave} onNext={() => goStage(3)} onBack={() => goStage(1)} />
            )}
            {current.id === 'validate' && (
              <ValidateStage onNext={() => goStage(4)} onBack={() => goStage(2)} />
            )}
            {current.id === 'review' && (
              <ReviewStage
                approved={approved}
                onApprove={markApproved}
                onBack={() => goStage(3)}
              />
            )}
            {current.id === 'qc' && (
              <QcStage
                qcPassed={qcPassed}
                onPass={markQc}
                onBack={() => goStage(4)}
              />
            )}
            {current.id === 'evidence' && (
              <EvidenceStage
                approved={approved}
                qcPassed={qcPassed}
                onBack={() => goStage(5)}
              />
            )}
          </section>
        </div>

        {/* Pane presets + tray toggle (D19 / D20) */}
        <div className="wb-footer">
          <div className="wb-tray-toggle" role="group" aria-label="Source or data pane">
            <span className="wb-presets-label">View</span>
            <button
              type="button"
              className={mobileTray === 'source' ? 'is-active' : ''}
              aria-pressed={mobileTray === 'source'}
              onClick={() => setMobileTray('source')}
            >
              Source
            </button>
            <button
              type="button"
              className={mobileTray === 'data' ? 'is-active' : ''}
              aria-pressed={mobileTray === 'data'}
              onClick={() => setMobileTray('data')}
            >
              Data
            </button>
          </div>
          <div className="wb-presets" role="group" aria-label="Pane width presets">
            <span className="wb-presets-label">Pane presets</span>
            {PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                className={p.id === preset ? 'is-active' : ''}
                aria-pressed={p.id === preset}
                onClick={() => setPreset(p.id)}
              >
                {p.id}
              </button>
            ))}
          </div>
          <div className="wb-guided">
            <button
              type="button"
              className={`wb-btn wb-btn-ghost${guided ? ' is-guided' : ''}`}
              onClick={() => setGuided((g) => !g)}
              aria-pressed={guided}
            >
              {guided ? 'Pause guided tour' : 'Watch the workflow'}
            </button>
            <span className="wb-foot-hint">Guided tour advances the stages automatically.</span>
          </div>
        </div>
      </div>
    </DemoFrame>
  );
}

function QueueStage({ onClaim }) {
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Assigned work</span>
      <h3>Batch {ITEM.batch} — {ITEM.title}</h3>
      <p className="wb-muted">
        This batch contains {ITEM.items} source documents. One item is opened at a
        time; each moves through extraction, mapping, validation, review, QC and
        evidence before it can be approved.
      </p>
      <ul className="wb-queue-list">
        <li><span className="wb-badge wb-badge-ok">Current</span> INV-2026-0417 — diesel invoice</li>
        <li>Invoice 0312 — red diesel</li>
        <li>Utility bill — Jan 2026</li>
        <li>Delivery notes — March</li>
      </ul>
      <div className="wb-stage-actions">
        <button type="button" className="wb-btn wb-btn-primary" onClick={onClaim}>
          Claim & start extraction
        </button>
      </div>
    </div>
  );
}

function ExtractStage({ linkedField, onLink, onSave, onNext }) {
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Extraction</span>
      <div className="wb-field-grid" role="list">
        {ITEM.extracted.fields.map((f) => (
          <div key={f.label} className="wb-field" role="listitem">
            <div className="wb-field-top">
              <span className="wb-field-label">{f.label}</span>
              <span className="wb-conf">{Math.round(f.confidence * 100)}%</span>
              <span className="wb-confbar" aria-hidden="true">
                <span style={{ width: `${f.confidence * 100}%` }} />
              </span>
            </div>
            <div className="wb-field-bottom">
              <input className="wb-input" defaultValue={f.value} aria-label={f.label} readOnly />
              <button
                type="button"
                className={`wb-linkbtn${linkedField === f.label ? ' is-linked' : ''}`}
                aria-pressed={linkedField === f.label}
                onClick={() => onLink(f.label)}
                title="Show where this value comes from in the source document"
              >
                <span aria-hidden="true">🔗</span> Link
              </button>
            </div>
          </div>
        ))}
      </div>
      <div className="wb-stage-actions">
        <button type="button" className="wb-btn" onClick={onSave}>Save draft</button>
        <button type="button" className="wb-btn wb-btn-primary" onClick={onNext}>Save extraction → Map</button>
      </div>
    </div>
  );
}

function MapStage({ onSave, onNext, onBack }) {
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Mapping &amp; emission factor</span>
      <p className="wb-muted">
        The activity <strong>Red diesel · 4,258.9 litres</strong> is matched against
        candidate factors. Every candidate and its match method is kept on the record.
      </p>
      <ul className="wb-factor-list">
        {[
          { name: 'Gas oil (red diesel)', src: 'DEFRA 2026', rate: '2.52 kg CO₂e / litre', method: 'Exact match — activity & unit', selected: true },
          { name: 'Diesel (average biofuel blend)', src: 'DEFRA 2026', rate: '2.52 kg CO₂e / litre', method: 'Similar fuel — different blend' },
          { name: 'Gas oil (red diesel)', src: 'DEFRA 2025', rate: '2.51 kg CO₂e / litre', method: 'Prior-year factor' },
        ].map((f) => (
          <li key={f.method} className={f.selected ? 'is-selected' : ''}>
            <div className="wb-factor-top">
              <span className="wb-factor-name">{f.name}</span>
              {f.selected ? <span className="wb-badge wb-badge-ok">Selected</span> : null}
            </div>
            <div className="wb-factor-sub">{f.src} · {f.rate}</div>
            <div className="wb-factor-method">{f.method}</div>
          </li>
        ))}
      </ul>
      <div className="wb-calc-note">
        4,258.9 litres × 2.52 kg CO₂e / litre = <strong>10,732.4 kg CO₂e</strong> (≈ 10.7 t CO₂e)
      </div>
      <div className="wb-stage-actions">
        <button type="button" className="wb-btn" onClick={onBack}>← Back</button>
        <button type="button" className="wb-btn" onClick={onSave}>Save</button>
        <button type="button" className="wb-btn wb-btn-primary" onClick={onNext}>Calculate → Validate</button>
      </div>
    </div>
  );
}

function ValidateStage({ onNext, onBack }) {
  const fails = VALIDATION_CHECKS.filter((c) => !c.ok).length;
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Validation</span>
      <div className="wb-validation-summary">
        <span className="wb-badge wb-badge-ok">{VALIDATION_CHECKS.length - fails} passed</span>
        <span className="wb-badge wb-badge-warn">{fails} attention</span>
        <span className="wb-muted">Automated checks · human-confirmed</span>
      </div>
      <ul className="wb-check-list">
        {VALIDATION_CHECKS.map((c) => (
          <li key={c.label} className={c.ok ? 'pass' : 'warn'}>
            <span className="wb-check-icon" aria-hidden="true">{c.ok ? '✓' : '!'}</span>
            <span>{c.label}</span>
            <span className="wb-badge wb-badge-neutral">{c.ok ? 'Pass' : 'Review'}</span>
          </li>
        ))}
      </ul>
      <p className="wb-muted">
        The unit mismatch routes the item back to mapping for confirmation — the
        reviewer confirms litres. This is the rework loop, not a new status.
      </p>
      <div className="wb-stage-actions">
        <button type="button" className="wb-btn" onClick={onBack}>← Back</button>
        <button type="button" className="wb-btn wb-btn-primary" onClick={onNext}>Confirmed → Review</button>
      </div>
    </div>
  );
}

function ReviewStage({ approved, onApprove, onBack }) {
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Review &amp; approval</span>
      <p className="wb-muted">
        Review is evidence-first: the result is checked against the source, factor and
        calculation before approval. Approval is a decision, not a data edit — it is
        recorded in the audit trail.
      </p>
      <ul className="wb-check-list">
        {REVIEW_CHECKS.map((c) => (
          <li key={c.label} className="pass">
            <span className="wb-check-icon" aria-hidden="true">✓</span>
            <span>{c.label}</span>
          </li>
        ))}
      </ul>
      {approved ? (
        <div className="wb-approved" aria-live="polite">
          <span className="wb-badge wb-badge-ok">Approved</span>
          <span>Result locked — snapshot {ITEM.result.snapshot} is immutable and traceable.</span>
        </div>
      ) : (
        <div className="wb-stage-actions">
          <button type="button" className="wb-btn wb-btn-danger" onClick={onBack}>Reject with reason</button>
          <button type="button" className="wb-btn wb-btn-primary" onClick={onApprove}>✓ Approve</button>
        </div>
      )}
    </div>
  );
}

function QcStage({ qcPassed, onPass, onBack }) {
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Quality control</span>
      <p className="wb-muted">
        CarbonTally performs a further QC pass before results are submitted to the
        customer. A processing entity may run its own review/QC for the work it
        performed.
      </p>
      <ul className="wb-check-list">
        {QC_CHECKS.map((c) => (
          <li key={c.label} className="pass">
            <span className="wb-check-icon" aria-hidden="true">✓</span>
            <span>{c.label}</span>
          </li>
        ))}
      </ul>
      {qcPassed ? (
        <div className="wb-approved" aria-live="polite">
          <span className="wb-badge wb-badge-ok">QC passed</span>
          <span>Ready for the customer review step.</span>
        </div>
      ) : (
        <div className="wb-stage-actions">
          <button type="button" className="wb-btn wb-btn-danger" onClick={onBack}>Send back to mapping</button>
          <button type="button" className="wb-btn wb-btn-primary" onClick={onPass}>✓ QC approve</button>
        </div>
      )}
    </div>
  );
}

function EvidenceStage({ approved, qcPassed, onBack }) {
  const complete = qcPassed;
  return (
    <div className="wb-stage">
      <span className="wb-stage-kicker">Evidence</span>
      <p className="wb-muted">
        Every number answers: <em>where did this come from?</em> The same completeness
        model applies to every result — Complete / Partial / Unavailable.
      </p>
      <ol className="wb-evidence" aria-label="Evidence chain">
        {EVIDENCE_CHAIN.map((e, i) => (
          <li key={e.title} style={{ '--i': i }}>
            <span className="wb-evidence-icon" aria-hidden="true">{e.icon}</span>
            <span className="wb-evidence-body">
              <strong>{e.title}</strong>
              <span>{e.detail}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="wb-evidence-status">
        <span className={`wb-badge ${complete ? 'wb-badge-ok' : 'wb-badge-warn'}`}>
          {complete ? 'Complete evidence chain' : 'Partial — QC pending'}
        </span>
        <span className={`wb-badge ${approved ? 'wb-badge-ok' : 'wb-badge-warn'}`}>
          {approved ? 'Customer approved' : 'Awaiting approval'}
        </span>
      </div>
      <div className="wb-stage-actions">
        <button type="button" className="wb-btn" onClick={onBack}>← Back</button>
      </div>
    </div>
  );
}
