// frontend/src/public/demos/HumanReviewDemo.jsx
// Demo D — "Human review / quality control".
// An extracted record with low confidence enters review. Validation findings
// are surfaced, a human reviewer confirms each check, and the record is
// approved. Public terminology only — no internal staff-role naming.
import React from 'react';
import { DemoFrame, DemoControls, useDemoRun, useInView, useAutoStart } from './demoCore';
import { INVOICE, REVIEW_FINDINGS, REVIEW_CHECKS, RESULT } from './demoData';

const STAGES = ['Extracted', 'Confidence', 'Needs review', 'Reviewed', 'Approved'];

export default function HumanReviewDemo() {
  const { step, started, start, done } = useDemoRun(STAGES.length, { stepMs: 1000 });
  const [ref, inView] = useInView(0.25);
  useAutoStart(inView, start);

  const findingsVisible = started && (done || step >= 2) ? REVIEW_FINDINGS.length : Math.max(0, step - 1);
  const checksVisible = done || step >= 3 ? REVIEW_CHECKS.length : Math.max(0, step - 3);

  return (
    <DemoFrame
      className="ct-demo-d"
      title="A human reviewer approves every result before it counts"
    >
      <div className="ct-demo-d-inner" ref={ref}>
        {/* Extracted record */}
        <div className="ct-demo-d-record">
          <span className="ct-demo-d-kicker">Extracted record</span>
          <span className="ct-demo-d-record-main">
            {INVOICE.item} · {INVOICE.qty} {INVOICE.unit}
          </span>
          <span className="ct-demo-d-record-meta">{INVOICE.supplier} · {INVOICE.date}</span>
          <div className={`ct-demo-d-conf ${started ? 'on' : ''}`}>
            <span className="ct-demo-d-conf-label">Automated confidence</span>
            <div className="ct-demo-d-confbar" aria-hidden="true">
              <span className="low" />
            </div>
            <span className="ct-demo-d-conf-num">0.71 — below review threshold</span>
          </div>
        </div>

        {/* Findings + review */}
        <div className="ct-demo-d-review">
          <div className="ct-demo-d-findings" aria-label="Validation findings">
            {REVIEW_FINDINGS.map((f, i) => (
              <div key={f.title} className={`ct-demo-d-finding ${i < findingsVisible ? 'on' : ''}`} style={{ '--i': i }}>
                <span className={`ct-demo-d-finding-level ${f.level}`} aria-hidden="true" />
                <div>
                  <div className="ct-demo-d-finding-title">{f.title}</div>
                  <div className="ct-demo-d-finding-detail">{f.detail}</div>
                </div>
              </div>
            ))}
          </div>

          <div className={`ct-demo-d-checks ${done || step >= 3 ? 'on' : ''}`} aria-label="Reviewer checks">
            {REVIEW_CHECKS.map((c, i) => (
              <div key={c.label} className={`ct-demo-d-check ${i < checksVisible ? 'on' : ''}`} style={{ '--i': i }}>
                <span className="ct-demo-d-check-icon" aria-hidden="true">✓</span>
                <span><strong>{c.label}</strong> — {c.detail}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={`ct-demo-d-status ${done ? 'on' : ''}`} aria-live="polite">
        <span className="ct-demo-status ct-demo-status-ok">Approved</span>
        <span className="ct-demo-d-status-text">
          Record approved and locked. The result ({RESULT.kg.toLocaleString('en-GB')} kg CO₂e for this line)
          is now eligible for reporting — with the review decision kept on the evidence record.
        </span>
      </div>

      <DemoControls started={started} done={done} step={step} steps={STAGES.length} onStart={start} label="Run the review" />
    </DemoFrame>
  );
}
