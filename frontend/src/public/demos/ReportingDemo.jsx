// frontend/src/public/demos/ReportingDemo.jsx
// Interactive reporting demonstration, based on the approved CarbonTally
// reporting UX. Shows the reporting period, emissions summary (scopes +
// categories), source information, evidence/traceability, calculation info
// and export/report actions. Fabricated, deterministic, local-only.
import React, { useState } from 'react';
import { DemoFrame } from './demoCore';
import './reporting.css';

const PERIODS = [
  {
    id: 'h1',
    label: 'Jan – Jun 2026',
    total: 128.0,
    records: 1284,
    verified: 1203,
    flagged: 81,
    documents: 342,
    scopes: [
      { name: 'Scope 1', value: 42.6, note: 'Owned fuel & gas', evidence: 'Complete' },
      { name: 'Scope 2', value: 18.3, note: 'Purchased electricity', evidence: 'Complete' },
      { name: 'Scope 3', value: 67.1, note: 'Supply chain & travel', evidence: 'Partial' },
    ],
    categories: [
      { name: 'Diesel (road)', value: 38.2 },
      { name: 'Business travel', value: 31.6 },
      { name: 'Waste', value: 21.2 },
      { name: 'Natural gas', value: 18.7 },
      { name: 'Electricity', value: 18.3 },
    ],
    snapshot: 'SNAP-2026-0177',
  },
  {
    id: 'h2',
    label: 'Jul – Dec 2026 (interim)',
    total: 114.5,
    records: 1160,
    verified: 1102,
    flagged: 38,
    documents: 305,
    scopes: [
      { name: 'Scope 1', value: 39.8, note: 'Owned fuel & gas', evidence: 'Complete' },
      { name: 'Scope 2', value: 17.6, note: 'Purchased electricity', evidence: 'Complete' },
      { name: 'Scope 3', value: 57.1, note: 'Supply chain & travel', evidence: 'Partial' },
    ],
    categories: [
      { name: 'Diesel (road)', value: 35.0 },
      { name: 'Business travel', value: 27.4 },
      { name: 'Waste', value: 19.8 },
      { name: 'Natural gas', value: 17.2 },
      { name: 'Electricity', value: 15.1 },
    ],
    snapshot: 'SNAP-2026-0234',
  },
];

const SOURCE_TYPES = [
  { name: 'Invoices & bills', count: 214 },
  { name: 'Scanned PDFs', count: 86 },
  { name: 'Spreadsheets (CSV / Excel)', count: 42 },
];

const EXPORTS = [
  { label: 'Emissions data (CSV)', current: true },
  { label: 'Documents index (CSV)', current: true },
  { label: 'Branded PDF report', current: true },
];

export default function ReportingDemo() {
  const [periodId, setPeriodId] = useState('h1');
  const [exported, setExported] = useState(null);
  const period = PERIODS.find((p) => p.id === periodId);
  const maxScope = Math.max(...period.scopes.map((s) => s.value));
  const maxCat = Math.max(...period.categories.map((c) => c.value));

  const doExport = (label) => {
    setExported(label);
    setTimeout(() => setExported(null), 2000);
  };

  return (
    <DemoFrame
      className="rd-frame"
      title="Reporting — a structured, evidence-backed report"
      note="Interactive demonstration — fabricated figures for a fictional organisation."
    >
      <div className="rd-app">
        <div className="rd-head">
          <div className="rd-head-id">
            <span className="rd-app-name">CarbonTally</span>
            <span className="rd-head-divider" aria-hidden="true">/</span>
            <strong>Aurora Foods Ltd — FY2026 emissions report</strong>
            <span className="rd-badge rd-badge-ok">Completed</span>
          </div>
          <div className="rd-period" role="group" aria-label="Reporting period">
            <span className="rd-period-label">Reporting period</span>
            {PERIODS.map((p) => (
              <button
                key={p.id}
                type="button"
                className={p.id === periodId ? 'is-active' : ''}
                aria-pressed={p.id === periodId}
                onClick={() => setPeriodId(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rd-body">
          <div className="rd-stats">
            <div className="rd-stat">
              <span className="rd-stat-label">Total footprint</span>
              <span className="rd-stat-value">{period.total.toFixed(1)} <small>t CO₂e</small></span>
            </div>
            <div className="rd-stat">
              <span className="rd-stat-label">Source records</span>
              <span className="rd-stat-value">{period.records.toLocaleString('en-GB')}</span>
            </div>
            <div className="rd-stat">
              <span className="rd-stat-label">Verified & approved</span>
              <span className="rd-stat-value">{period.verified.toLocaleString('en-GB')}</span>
            </div>
            <div className="rd-stat">
              <span className="rd-stat-label">Flagged for review</span>
              <span className="rd-stat-value">{period.flagged}</span>
            </div>
          </div>

          <div className="rd-grid rd-grid-2">
            <section className="rd-panel" aria-labelledby="rd-scopes">
              <div className="rd-panel-head">
                <h3 id="rd-scopes">Emissions by scope</h3>
              </div>
              <div className="rd-scopes">
                {period.scopes.map((s) => (
                  <div key={s.name} className="rd-scope">
                    <div className="rd-scope-head">
                      <span className="rd-scope-name">{s.name}</span>
                      <span className="rd-scope-value">{s.value.toFixed(1)} <small>t CO₂e</small></span>
                    </div>
                    <div className="rd-track">
                      <span className="rd-fill" style={{ width: `${(s.value / maxScope) * 100}%` }} />
                    </div>
                    <div className="rd-scope-foot">
                      <span className="rd-scope-note">{s.note}</span>
                      <span className={`rd-badge ${s.evidence === 'Complete' ? 'rd-badge-ev' : 'rd-badge-warn'}`}>
                        Evidence: {s.evidence}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rd-panel" aria-labelledby="rd-cats">
              <div className="rd-panel-head">
                <h3 id="rd-cats">Emissions by category</h3>
              </div>
              <div className="rd-cats">
                {period.categories.map((c) => (
                  <div key={c.name} className="rd-cat">
                    <span className="rd-cat-name">{c.name}</span>
                    <div className="rd-track">
                      <span className="rd-fill" style={{ width: `${(c.value / maxCat) * 100}%` }} />
                    </div>
                    <span className="rd-cat-value">{c.value.toFixed(1)} t</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="rd-grid rd-grid-3">
            <section className="rd-panel" aria-labelledby="rd-sources">
              <div className="rd-panel-head">
                <h3 id="rd-sources">Source information</h3>
              </div>
              <ul className="rd-list">
                {SOURCE_TYPES.map((t) => (
                  <li key={t.name} className="rd-list-item">
                    <span className="rd-list-main">{t.name}</span>
                    <span className="rd-list-meta">{t.count}</span>
                  </li>
                ))}
              </ul>
              <p className="rd-note">Source documents stay in private, organisation-scoped storage.</p>
            </section>

            <section className="rd-panel" aria-labelledby="rd-calc">
              <div className="rd-panel-head">
                <h3 id="rd-calc">Calculation information</h3>
              </div>
              <p className="rd-calc-line">
                4,258.9 litres × 2.52 kg CO₂e / litre = <strong>10,732.4 kg CO₂e</strong>
              </p>
              <p className="rd-note">
                Calculated by the server-authoritative engine and recorded as an immutable
                snapshot (<span className="rd-mono">{period.snapshot}</span>) at the moment of calculation.
              </p>
            </section>

            <section className="rd-panel" aria-labelledby="rd-trace">
              <div className="rd-panel-head">
                <h3 id="rd-trace">Traceability</h3>
              </div>
              <ul className="rd-list">
                <li className="rd-list-item">
                  <span className="rd-list-main">Every result traces back</span>
                  <span className="rd-badge rd-badge-ev">Complete</span>
                </li>
                <li className="rd-list-item">
                  <span className="rd-list-main">Partial coverage (Scope 3)</span>
                  <span className="rd-badge rd-badge-warn">Partial</span>
                </li>
                <li className="rd-list-item">
                  <span className="rd-list-main">Unavailable evidence</span>
                  <span className="rd-badge rd-badge-neutral">Unavailable</span>
                </li>
              </ul>
              <p className="rd-note">The same Source → Extract → Map → Factor → Calculate → Evidence chain applies to every number.</p>
            </section>
          </div>
        </div>

        <div className="rd-actions">
          <span className="rd-actions-label">Export / report actions</span>
          {EXPORTS.map((e) => (
            <button
              key={e.label}
              type="button"
              className={`rd-btn${e.current ? ' rd-btn-primary' : ''}`}
              onClick={() => doExport(e.label)}
            >
              {e.label}
              {!e.current ? <span className="rd-btn-note">planned</span> : null}
            </button>
          ))}
          <span className="rd-export-status" aria-live="polite">
            {exported ? `Exported: ${exported} (demo)` : ''}
          </span>
        </div>
      </div>
    </DemoFrame>
  );
}
