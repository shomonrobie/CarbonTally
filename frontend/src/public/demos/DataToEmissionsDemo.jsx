// frontend/src/public/demos/DataToEmissionsDemo.jsx
// Demo A — "Messy data → structured emissions".
// One messy source line flows through the real CarbonTally pipeline
// (clean -> activity -> factor match -> calculation) into a structured row.
import React from 'react';
import { DemoFrame, DemoControls, StageRail, useDemoRun, useInView, useAutoStart } from './demoCore';
import { RAW_LINE, INVOICE, FACTOR, RESULT } from './demoData';

const STAGES = ['Raw record', 'Cleaned', 'Activity', 'Factor', 'Calculated'];

const CLEANED = [
  ['Date', '06 Mar 2026'],
  ['Description', 'Red diesel delivery'],
  ['Site', 'Birmingham Hub'],
  ['Fuel / activity', 'Red diesel'],
  ['Quantity', '4,258.9'],
  ['Unit', 'litres'],
];

export default function DataToEmissionsDemo() {
  const { step, started, start, done } = useDemoRun(STAGES.length, { stepMs: 1050 });
  const [ref, inView] = useInView(0.25);
  useAutoStart(inView, start);

  const active = (i) => (done || step > i) && started;

  return (
    <DemoFrame
      className="ct-demo-a"
      title="One messy line → one calculated, evidenced result"
    >
      <div className="ct-demo-a-inner" ref={ref}>
        {/* Left: the raw record */}
        <div className={`ct-demo-a-raw ${started ? 'consumed' : ''}`}>
          <span className="ct-demo-a-kicker">Invoice line (INV-2026-0417)</span>
          <code className="ct-demo-a-code">{RAW_LINE}</code>
          <p>Untidy, abbreviated, mixed formats — the kind of record a human has to interpret.</p>
        </div>

        {/* Middle: stage rail */}
        <div className="ct-demo-a-rail">
          <StageRail labels={STAGES} step={step} done={done} />
        </div>

        {/* Right: the transformed record */}
        <div className="ct-demo-a-out">
          <table className={`ct-demo-table ${active(5) ? 'filled' : ''}`} aria-label="Structured result">
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {CLEANED.map(([k, v], idx) => (
                <tr key={k} className={active(1) ? 'on' : ''} style={{ '--i': idx }}>
                  <td>{k}</td>
                  <td>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className={`ct-demo-a-calc ${active(3) ? 'on' : ''}`}>
            <span>
              Activity matched: <strong>{FACTOR.name}</strong> — {FACTOR.provider} {FACTOR.year},{' '}
              {FACTOR.rate} {FACTOR.unit} ({FACTOR.method})
            </span>
            <span className="ct-demo-a-formula">
              {INVOICE.qty.replace(/,/g, '')} {INVOICE.unit} × {FACTOR.rate.toFixed(2)} kg CO₂e / {INVOICE.unit} ={' '}
              <strong>{RESULT.kg.toLocaleString('en-GB')} kg CO₂e</strong>
            </span>
          </div>
        </div>
      </div>

      <div className={`ct-demo-a-result ${active(4) ? 'on' : ''}`} aria-live="polite">
        <span className="ct-demo-a-result-label">Result</span>
        <span className="ct-demo-a-result-value">{RESULT.kg.toLocaleString('en-GB')} kg CO₂e</span>
        <span className="ct-demo-a-result-sub">≈ {RESULT.tonnes} t CO₂e · snapshotted & traceable</span>
      </div>

      <DemoControls started={started} done={done} step={step} steps={STAGES.length} onStart={start} label="Run the demo" />
    </DemoFrame>
  );
}
