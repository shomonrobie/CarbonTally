// frontend/src/public/demos/demoCore.jsx
// Shared building blocks for the public interactive demos.
// All demos are local-only: fabricated data, processed in the browser,
// nothing uploaded, nothing stored, no backend calls.
import React, { useCallback, useEffect, useRef, useState } from 'react';

export const DEMO_NOTE = 'Interactive demonstration';

export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
    const onChange = (e) => setReduced(e.matches);
    mq.addEventListener ? mq.addEventListener('change', onChange) : mq.addListener(onChange);
    return () => {
      mq.removeEventListener ? mq.removeEventListener('change', onChange) : mq.removeListener(onChange);
    };
  }, []);
  return reduced;
}

export function useInView(threshold = 0.3) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === 'undefined') return undefined;
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setInView(true)),
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return [ref, inView];
}

// Steps a run through `steps` stages. Reduced motion jumps straight to the end.
export function useDemoRun(steps, { stepMs = 900 } = {}) {
  const reduced = usePrefersReducedMotion();
  const [started, setStarted] = useState(false);
  const [step, setStep] = useState(0);

  const start = useCallback(() => {
    setStarted(true);
    setStep(0);
  }, []);

  useEffect(() => {
    if (!started) return undefined;
    if (reduced) {
      setStep(steps);
      return undefined;
    }
    if (step >= steps) return undefined;
    const t = setTimeout(() => setStep((s) => Math.min(s + 1, steps)), stepMs);
    return () => clearTimeout(t);
  }, [started, step, steps, stepMs, reduced]);

  return { step, started, start, reduced, done: started && step >= steps };
}

// Auto-starts a demo once when its container scrolls into view.
export function useAutoStart(inView, start) {
  const doneRef = useRef(false);
  useEffect(() => {
    if (inView && !doneRef.current) {
      doneRef.current = true;
      start();
    }
  }, [inView, start]);
}

export function DemoFrame({ title, children, note = DEMO_NOTE, className = '' }) {
  return (
    <div className={`ct-demo ${className}`}>
      <div className="ct-demo-topline">
        <span className="ct-demo-pill">
          <span className="ct-demo-pill-dot" aria-hidden="true" /> Interactive demonstration
        </span>
        {title ? <span className="ct-demo-title">{title}</span> : null}
      </div>
      {children}
      <p className="ct-demo-note">{note}</p>
    </div>
  );
}

export function StageRail({ labels, step, done }) {
  return (
    <ol className="ct-demo-rail" aria-label="Processing stages">
      {labels.map((label, i) => {
        const reached = done || i < step;
        return (
          <li key={label} className={reached ? 'on' : ''}>
            <span className="ct-demo-rail-dot" aria-hidden="true">{reached ? '✓' : ''}</span>
            <span className="ct-demo-rail-label">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}

export function DemoControls({ started, done, step, steps, onStart, label = 'Run the demo' }) {
  const busy = started && !done;
  return (
    <div className="ct-demo-controls">
      <button type="button" className="ct-btn ct-btn-primary" onClick={onStart} aria-live="polite">
        {!started ? label : done ? 'Replay' : `Processing ${Math.min(step, steps)} / ${steps}…`}
      </button>
      {busy ? (
        <span className="ct-demo-busy" role="status" aria-live="polite">Working…</span>
      ) : null}
    </div>
  );
}

// Eased count-up for totals. Respects prefers-reduced-motion.
export function useCountUp(target, { active, duration = 900, decimals = 1 } = {}) {
  const reduced = usePrefersReducedMotion();
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!active) {
      setValue(0);
      return undefined;
    }
    if (reduced) {
      setValue(target);
      return undefined;
    }
    const from = performance.now();
    let raf;
    const tick = (now) => {
      const p = Math.min((now - from) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(target * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, target, duration, reduced]);
  return value;
}

export function StatusBadge({ children, tone = 'ok' }) {
  return <span className={`ct-demo-status ct-demo-status-${tone}`}>{children}</span>;
}
