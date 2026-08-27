// frontend/src/public/demos/EvidenceTraceabilityDemo.jsx
// Demo E — "Evidence traceability".
// One emissions number unwinds to its full evidence chain: calculation ->
// factor -> extracted line -> source document -> method. Mirrors the D33.1
// evidence record and its COMPLETE/PARTIAL/UNAVAILABLE completeness model.
import React from 'react';
import { DemoFrame, DemoControls, useDemoRun, useInView, useAutoStart } from './demoCore';
import { EVIDENCE_CHAIN, RESULT } from './demoData';

const STAGES = ['Number', 'Calculation', 'Factor', 'Extracted line', 'Document'];

export default function EvidenceTraceabilityDemo() {
  const { step, started, start, done } = useDemoRun(STAGES.length, { stepMs: 900 });
  const [ref, inView] = useInView(0.25);
  useAutoStart(inView, start);

  const nodesVisible = started ? (done ? EVIDENCE_CHAIN.length : Math.max(0, step - 1)) : 0;

  return (
    <DemoFrame
      className="ct-demo-e"
      title="Every number can answer: where did this come from?"
    >
      <div className="ct-demo-e-inner" ref={ref}>
        {/* The number */}
        <div className={`ct-demo-e-number ${started ? 'on' : ''}`}>
          <span className="ct-demo-e-kicker">Emissions result</span>
          <span className="ct-demo-e-value">{RESULT.kg.toLocaleString('en-GB')} kg CO₂e</span>
          <span className="ct-demo-e-sub">≈ {RESULT.tonnes} t CO₂e · diesel delivery, 2026 (demo)</span>
        </div>

        {/* The chain */}
        <ol className="ct-demo-e-chain" aria-label="Evidence chain">
          {EVIDENCE_CHAIN.map((node, i) => {
            const on = i < nodesVisible;
            return (
              <li key={node.title} className={on ? 'on' : ''} style={{ '--i': i }}>
                <span className="ct-demo-e-chain-icon" aria-hidden="true">{node.icon}</span>
                <span className="ct-demo-e-chain-body">
                  <span className="ct-demo-e-chain-title">{node.title}</span>
                  <span className="ct-demo-e-chain-detail">{on ? node.detail : '…'}</span>
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      <div className={`ct-demo-e-foot ${done ? 'on' : ''}`} aria-live="polite">
        <span className="ct-demo-status ct-demo-status-ok">Complete evidence chain</span>
        <span>
          Document + extracted line + source page + emission factor + calculation — the same
          completeness model CarbonTally applies to every result (Complete / Partial / Unavailable).
        </span>
      </div>

      <DemoControls started={started} done={done} step={step} steps={STAGES.length} onStart={start} label="Trace the number" />
    </DemoFrame>
  );
}
