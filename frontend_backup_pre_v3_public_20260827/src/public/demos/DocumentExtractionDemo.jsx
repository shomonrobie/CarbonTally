// frontend/src/public/demos/DocumentExtractionDemo.jsx
// Demo B — "Document → extracted data".
// A fictional invoice is "read" and structured fields appear one by one with
// confidence. Ends in a ready-for-review status. Entirely local: nothing is
// sent to an OCR or AI service.
import React from 'react';
import { DemoFrame, DemoControls, useDemoRun, useInView, useAutoStart } from './demoCore';
import { INVOICE, EXTRACTED_FIELDS } from './demoData';

const STAGES = ['Document', 'Extraction', 'Fields detected', 'Structured', 'Review'];

export default function DocumentExtractionDemo() {
  const { step, started, start, done } = useDemoRun(STAGES.length, { stepMs: 900 });
  const [ref, inView] = useInView(0.25);
  useAutoStart(inView, start);

  // Fields appear from stage 1 onward, one per tick.
  const visibleFields = done ? EXTRACTED_FIELDS.length : Math.max(0, step - 1);

  return (
    <DemoFrame
      className="ct-demo-b"
      title="A PDF invoice becomes structured, reviewable fields"
    >
      <div className="ct-demo-b-inner" ref={ref}>
        {/* The document */}
        <div className={`ct-demo-b-doc ${started ? 'read' : ''}`}>
          <div className="ct-demo-b-doc-head">
            <span>Meridian Fuel Supplies Ltd</span>
            <span className="ct-demo-b-doc-ref">INV-2026-0417</span>
          </div>
          <div className="ct-demo-b-doc-line">Invoice date · {INVOICE.date}</div>
          <div className="ct-demo-b-doc-line">Deliver to · {INVOICE.site}</div>
          <div className="ct-demo-b-doc-line">RED DIESEL · {INVOICE.qty} L · {INVOICE.amount}</div>
          <div className="ct-demo-b-doc-line muted">Delivery note 3021</div>
          {started ? <div className="ct-demo-b-scan" aria-hidden="true" /> : null}
        </div>

        {/* Extracted fields */}
        <div className="ct-demo-b-fields">
          {EXTRACTED_FIELDS.map((f, i) => {
            const on = i < visibleFields;
            return (
              <div key={f.label} className={`ct-demo-b-field ${on ? 'on' : ''}`}>
                <div className="ct-demo-b-field-top">
                  <span className="ct-demo-b-field-label">{f.label}</span>
                  <span className="ct-demo-b-field-conf">{on ? `${Math.round(f.confidence * 100)}%` : ''}</span>
                </div>
                <div className="ct-demo-b-field-value">{on ? f.value : '…'}</div>
                <div className="ct-demo-b-confbar" aria-hidden="true">
                  <span style={{ width: on ? `${f.confidence * 100}%` : '0%' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className={`ct-demo-b-status ${done ? 'on' : ''}`} aria-live="polite">
        <span className="ct-demo-status ct-demo-status-warn">Ready for review</span>
        <span className="ct-demo-b-status-text">
          Fields were drafted from the document (locally, for the demo). A reviewer confirms them
          before the record moves to mapping — see Human Processing Services.
        </span>
      </div>

      <DemoControls started={started} done={done} step={step} steps={STAGES.length} onStart={start} label="Extract fields" />
    </DemoFrame>
  );
}
