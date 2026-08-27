// frontend/src/v3/components/ui/Tabs.jsx
// D21.9 — accessible tab list (roving tabindex, aria-selected, keyboard nav).
import React from 'react';
import './ui.css';

export default function Tabs({ tabs, active, onChange, ariaLabel }) {
  const refs = React.useRef([]);

  const onKeyDown = (e, index) => {
    const count = tabs.length;
    let next = null;
    if (e.key === 'ArrowRight') next = (index + 1) % count;
    if (e.key === 'ArrowLeft') next = (index - 1 + count) % count;
    if (e.key === 'Home') next = 0;
    if (e.key === 'End') next = count - 1;
    if (next === null) return;
    e.preventDefault();
    onChange(tabs[next].id);
    refs.current[next]?.focus();
  };

  return (
    <div className="ct-tabs" role="tablist" aria-label={ariaLabel}>
      {tabs.map((tab, i) => (
        <button
          key={tab.id}
          ref={(el) => { refs.current[i] = el; }}
          type="button"
          role="tab"
          id={`ct-tab-${tab.id}`}
          aria-controls={`ct-tabpanel-${tab.id}`}
          aria-selected={active === tab.id}
          tabIndex={active === tab.id ? 0 : -1}
          className="ct-tabs__tab"
          onClick={() => onChange(tab.id)}
          onKeyDown={(e) => onKeyDown(e, i)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
