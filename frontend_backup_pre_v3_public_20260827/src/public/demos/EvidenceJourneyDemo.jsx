// frontend/src/public/demos/EvidenceJourneyDemo.jsx
// Landing-page evidence demonstration: one example record traced through
// Source -> Extract -> Map -> Calculate -> Validate -> Result. Every stage is
// clickable and shows the relevant part of the same record, so visitors can
// follow a single invoice from source document to evidenced result.
import React, { useRef, useState } from 'react';
import { INVOICE, FACTOR, RESULT } from './demoData';

const STAGES = ['Source', 'Extract', 'Map', 'Calculate', 'Validate'];

const CHECKS = [
  'Source recorded',
  'Factor identified',
  'Calculation captured',
  'Evidence traceable',
];

export default function EvidenceJourneyDemo() {
  const [active, setActive] = useState(0);
  const tabsRef = useRef(null);

  const onKeyDown = (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    e.preventDefault();
    const next =
      e.key === 'ArrowRight'
        ? (active + 1) % STAGES.length
        : (active - 1 + STAGES.length) % STAGES.length;
    setActive(next);
    const btns = tabsRef.current ? tabsRef.current.querySelectorAll('button') : [];
    if (btns[next]) btns[next].focus();
  };

  return (
    <div className="ct-evj">
      <div className="ct-evj-head">
        <span className="ct-demo-pill">
          <span className="ct-demo-pill-dot" aria-hidden="true" /> Interactive demonstration
        </span>
        <span className="ct-evj-status">Validated</span>
      </div>

      <div
        className="ct-evj-tabs"
        role="tablist"
        aria-label="Record journey stages"
        ref={tabsRef}
        onKeyDown={onKeyDown}
      >
        {STAGES.map((label, i) => (
          <button
            key={label}
            type="button"
            role="tab"
            id={`ct-evj-tab-${i}`}
            aria-selected={active === i}
            aria-controls="ct-evj-panel"
            tabIndex={active === i ? 0 : -1}
            className={active === i ? 'on' : ''}
            onClick={() => setActive(i)}
          >
            {label}
          </button>
        ))}
      </div>

      <div
        className="ct-evj-panel"
        role="tabpanel"
        id="ct-evj-panel"
        aria-labelledby={`ct-evj-tab-${active}`}
      >
        {active === 0 && (
          <div className="ct-evj-block">
            <span className="ct-evj-kicker">Source document</span>
            <div className="ct-evj-doc">
              <div className="ct-evj-doc-title">Invoice {INVOICE.ref}</div>
              <div className="ct-evj-doc-meta">{INVOICE.supplier}</div>
              <div className="ct-evj-doc-lines">
                <span>{INVOICE.item}</span>
                <span>{INVOICE.qty} L</span>
                <span>{INVOICE.amount}</span>
              </div>
            </div>
          </div>
        )}

        {active === 1 && (
          <div className="ct-evj-block">
            <span className="ct-evj-kicker">Extracted activity data</span>
            <dl className="ct-evj-fields">
              <div><dt>Vendor</dt><dd>{INVOICE.supplier}</dd></div>
              <div><dt>Quantity</dt><dd>{INVOICE.qty} L</dd></div>
              <div><dt>Amount</dt><dd>{INVOICE.amount}</dd></div>
              <div><dt>Date</dt><dd>{INVOICE.date}</dd></div>
            </dl>
          </div>
        )}

        {active === 2 && (
          <div className="ct-evj-block">
            <span className="ct-evj-kicker">Emission factor</span>
            <dl className="ct-evj-fields">
              <div><dt>Activity</dt><dd>{FACTOR.name}</dd></div>
              <div><dt>Emission factor</dt><dd>{FACTOR.provider} {FACTOR.year} · {FACTOR.rate.toFixed(2)} kg CO₂e / litre</dd></div>
            </dl>
          </div>
        )}

        {active === 3 && (
          <div className="ct-evj-block">
            <span className="ct-evj-kicker">Calculation</span>
            <div className="ct-evj-calc">
              <span>{INVOICE.qty} L</span>
              <i>×</i>
              <span>{FACTOR.rate.toFixed(2)} kg CO₂e / L</span>
              <i>=</i>
              <strong>{RESULT.kg.toLocaleString('en-GB')} kg CO₂e</strong>
            </div>
          </div>
        )}

        {active === 4 && (
          <div className="ct-evj-block">
            <span className="ct-evj-kicker">Validation &amp; review</span>
            <ul className="ct-evj-checks">
              {CHECKS.map((c) => (
                <li key={c}><span aria-hidden="true">✓</span>{c}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="ct-evj-result">
        <div className="ct-evj-result-num">
          {RESULT.kg.toLocaleString('en-GB')} <span>kg CO₂e</span>
        </div>
        <div className="ct-evj-result-sub">≈ {RESULT.tonnes} t CO₂e · fully evidenced</div>
      </div>
    </div>
  );
}
