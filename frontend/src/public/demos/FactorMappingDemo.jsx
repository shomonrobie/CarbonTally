// frontend/src/public/demos/FactorMappingDemo.jsx
// Demo C — "Mapping & emission factor".
// An activity is matched against candidate emission factors. Candidates appear
// with their match method and confidence; the selected factor is highlighted,
// then the calculation runs. Mirrors the real factor-matching pipeline
// (exact -> alias -> fuzzy -> semantic stages with confidence + provenance).
import React from 'react';
import { DemoFrame, DemoControls, useDemoRun, useInView, useAutoStart } from './demoCore';
import { INVOICE, CANDIDATE_FACTORS, WHY_FACTOR_SELECTED, FACTOR, RESULT } from './demoData';

const STAGES = ['Activity', 'Candidates', 'Selected', 'Calculated'];

export default function FactorMappingDemo() {
  const { step, started, start, done } = useDemoRun(STAGES.length, { stepMs: 1100 });
  const [ref, inView] = useInView(0.25);
  useAutoStart(inView, start);

  const candidatesVisible = done || step >= 2 ? CANDIDATE_FACTORS.length : Math.max(0, step - 1);
  const selected = done || step >= 3;

  return (
    <DemoFrame
      className="ct-demo-c"
      title="Why this factor? Every candidate is kept on the record"
    >
      <div className="ct-demo-c-inner" ref={ref}>
        {/* Activity */}
        <div className="ct-demo-c-activity">
          <span className="ct-demo-c-kicker">Activity</span>
          <span className="ct-demo-c-activity-value">
            {INVOICE.item} — {INVOICE.qty} {INVOICE.unit}
          </span>
          <span className="ct-demo-c-activity-meta">From invoice INV-2026-0417 · Birmingham Hub</span>
        </div>

        {/* Candidate factors */}
        <ul className="ct-demo-c-candidates" aria-label="Candidate emission factors">
          {CANDIDATE_FACTORS.map((f, i) => {
            const on = i < candidatesVisible;
            return (
              <li
                key={`${f.source} · ${f.name}`}
                className={`${on ? 'on' : ''} ${f.selected && selected ? 'picked' : ''}`}
                style={{ '--i': i }}
              >
                <div className="ct-demo-c-cand-top">
                  <span className="ct-demo-c-cand-name">{f.name}</span>
                  {f.selected && selected ? (
                    <span className="ct-demo-status ct-demo-status-ok">Selected</span>
                  ) : (
                    <span className="ct-demo-c-cand-conf">{on ? `${Math.round(f.confidence * 100)}%` : ''}</span>
                  )}
                </div>
                <div className="ct-demo-c-cand-sub">
                  {f.source} · {f.rate}
                </div>
                <div className="ct-demo-c-cand-method">{on ? f.method : ''}</div>
              </li>
            );
          })}
        </ul>

        {/* Calculation */}
        <div className={`ct-demo-c-calc ${selected ? 'on' : ''}`} aria-live="polite">
          <div className="ct-demo-c-calc-line">
            {INVOICE.qty} {INVOICE.unit} × <strong>{FACTOR.rate.toFixed(2)} kg CO₂e / litre</strong>
          </div>
          <div className="ct-demo-c-calc-line result">
            = <strong>{RESULT.kg.toLocaleString('en-GB')} kg CO₂e</strong> (≈ {RESULT.tonnes} t CO₂e)
          </div>
          <div className="ct-demo-c-calc-why">{WHY_FACTOR_SELECTED}</div>
        </div>
      </div>

      <DemoControls started={started} done={done} step={step} steps={STAGES.length} onStart={start} label="Match a factor" />
    </DemoFrame>
  );
}
