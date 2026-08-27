// frontend/src/public/demos/DashboardDemo.jsx
// Demo F — "Dashboard / reporting result".
// Verified records roll up into Scope 1/2/3 totals, categories and a trend.
// Totals animate from zero as the dashboard "builds" — the same rollup the
// platform produces from approved records. All figures are fabricated.
import React from 'react';
import { DemoFrame, DemoControls, useDemoRun, useInView, useAutoStart, useCountUp } from './demoCore';
import { DASHBOARD } from './demoData';

const STAGES = ['Records', 'Scopes', 'Categories', 'Trend'];

function Stat({ label, value, active, format, sub }) {
  const v = useCountUp(value, { active, duration: 1100, decimals: 0 });
  return (
    <div className={`ct-demo-f-stat ${active ? 'on' : ''}`}>
      <span className="ct-demo-f-stat-label">{label}</span>
      <span className="ct-demo-f-stat-value">{format ? format(v) : Math.round(v).toLocaleString('en-GB')}</span>
      {sub ? <span className="ct-demo-f-stat-sub">{sub}</span> : null}
    </div>
  );
}

function ScopeCard({ scope, active, index }) {
  const v = useCountUp(scope.value, { active, duration: 1000 + index * 150, decimals: 1 });
  return (
    <div className={`ct-demo-f-scope ${active ? 'on' : ''}`} style={{ '--i': index }}>
      <span className="ct-demo-f-scope-name">{scope.name}</span>
      <span className="ct-demo-f-scope-value">{v.toFixed(1)} <small>t CO₂e</small></span>
      <span className="ct-demo-f-scope-note">{scope.note}</span>
    </div>
  );
}

export default function DashboardDemo() {
  const { step, started, start, done } = useDemoRun(STAGES.length, { stepMs: 900 });
  const [ref, inView] = useInView(0.2);
  useAutoStart(inView, start);

  const active1 = started && (done || step >= 1); // scopes
  const active2 = started && (done || step >= 2); // categories
  const active3 = started && (done || step >= 3); // trend
  const total = useCountUp(DASHBOARD.total, { active: active1, duration: 1400, decimals: 1 });
  const records = useCountUp(DASHBOARD.records, { active: started, duration: 1600, decimals: 0 });
  const verified = useCountUp(DASHBOARD.verified, { active: started, duration: 1600, decimals: 0 });
  const maxCat = Math.max(...DASHBOARD.categories.map((c) => c.value));
  const maxTrend = Math.max(...DASHBOARD.trend.map((t) => t.value));

  return (
    <DemoFrame
      className="ct-demo-f"
      title={`${DASHBOARD.company} — ${DASHBOARD.period}`}
    >
      <div className="ct-demo-f-inner" ref={ref}>
        <div className="ct-demo-f-stats">
          <Stat label="Records processed" value={DASHBOARD.records} active={started} />
          <Stat label="Verified & approved" value={DASHBOARD.verified} active={started} />
          <Stat label="Flagged for review" value={DASHBOARD.flagged} active={started} />
        </div>

        <div className="ct-demo-f-main">
          <div className="ct-demo-f-scopes" aria-label="Emissions by scope">
            <div className={`ct-demo-f-total ${active1 ? 'on' : ''}`}>
              <span className="ct-demo-f-total-label">Total footprint</span>
              <span className="ct-demo-f-total-value">{total.toFixed(1)} <small>t CO₂e</small></span>
            </div>
            {DASHBOARD.scopes.map((s, i) => (
              <ScopeCard key={s.name} scope={s} active={active1} index={i} />
            ))}
          </div>

          <div className="ct-demo-f-cats" aria-label="Emissions by category">
            <span className="ct-demo-f-section-label">By category</span>
            {DASHBOARD.categories.map((c, i) => (
              <div key={c.name} className="ct-demo-f-cat" style={{ '--i': i }}>
                <span className="ct-demo-f-cat-name">{c.name}</span>
                <div className="ct-demo-f-cat-track">
                  <span
                    className="ct-demo-f-cat-fill"
                    style={{ width: active2 ? `${(c.value / maxCat) * 100}%` : '0%' }}
                  />
                </div>
                <span className="ct-demo-f-cat-value">{active2 ? `${c.value.toFixed(1)} t` : ''}</span>
              </div>
            ))}
          </div>

          <div className="ct-demo-f-trend" aria-label="Monthly trend">
            <span className="ct-demo-f-section-label">Monthly trend (t CO₂e)</span>
            <div className="ct-demo-f-trend-chart">
              {DASHBOARD.trend.map((m, i) => (
                <div key={m.month} className="ct-demo-f-trend-col" style={{ '--i': i }}>
                  <span className="ct-demo-f-trend-val">{active3 ? m.value.toFixed(1) : ''}</span>
                  <div className="ct-demo-f-trend-track">
                    <span
                      className="ct-demo-f-trend-fill"
                      style={{ height: active3 ? `${(m.value / maxTrend) * 100}%` : '0%' }}
                    />
                  </div>
                  <span className="ct-demo-f-trend-month">{m.month}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <p className="ct-demo-f-note">
          {records.toLocaleString('en-GB')} records · {verified.toLocaleString('en-GB')} verified ·{' '}
          {active1 ? `${total.toFixed(1)} t CO₂e total` : 'totals build from approved records'}
        </p>
      </div>

      <DemoControls started={started} done={done} step={step} steps={STAGES.length} onStart={start} label="Build the dashboard" />
    </DemoFrame>
  );
}
