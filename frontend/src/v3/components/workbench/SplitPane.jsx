// frontend/src/v3/components/workbench/SplitPane.jsx
// D19 — split-pane primitive with the three approved presets (40/60, 50/50,
// 60/40) plus a draggable divider that overrides the preset. On tablet/mobile
// the panes collapse to a tray flow (handled by WorkbenchShell).
import React, { useRef, useState } from 'react';

export const PRESETS = ['40-60', '50-50', '60-40'];

export default function SplitPane({ left, right, preset = '50-50', leftLabel = 'Source', rightLabel = 'Data' }) {
  const containerRef = useRef(null);
  const [customRatio, setCustomRatio] = useState(null);
  const dragging = useRef(false);

  const onPointerDown = (e) => {
    e.preventDefault();
    dragging.current = true;
    const onMove = (event) => {
      if (!dragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const ratio = Math.min(0.75, Math.max(0.25, (event.clientX - rect.left) / rect.width));
      setCustomRatio(ratio);
    };
    const onUp = () => {
      dragging.current = false;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  };

  // Keyboard-accessible resizing: the divider is a focusable button; ArrowLeft /
  // ArrowRight adjust the split by 5% within the approved 25–75% range.
  const onKeyDown = (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    setCustomRatio((r) => {
      const current = r ?? { '40-60': 40, '50-50': 50, '60-40': 60 }[preset] ?? 50;
      const next = e.key === 'ArrowLeft' ? current - 5 : current + 5;
      return Math.min(75, Math.max(25, next)) / 100;
    });
  };

  const leftPct = customRatio ? customRatio * 100 : { '40-60': 40, '50-50': 50, '60-40': 60 }[preset] ?? 50;

  const paneStyle = (isLeft) => ({
    flex: `0 1 ${isLeft ? leftPct : 100 - leftPct}%`,
    maxWidth: isLeft ? `${leftPct}%` : `${100 - leftPct}%`,
    minWidth: 0,
  });

  const renderPane = (content, ariaLabel, isLeft) => (
    <section className="ct-pane" aria-label={ariaLabel} style={paneStyle(isLeft)}>
      {content}
    </section>
  );

  return (
    <div
      ref={containerRef}
      className="ct-wb-panes"
      role="group"
      aria-label={`Split view: ${leftLabel} / ${rightLabel}`}
    >
      {renderPane(left, leftLabel, true)}
      <button
        type="button"
        className="ct-wb-resize-handle"
        aria-label="Resize panes"
        title="Drag, or focus and press Left/Right arrow to resize (5% steps)"
        onPointerDown={onPointerDown}
        onKeyDown={onKeyDown}
      >
        ⋮
      </button>
      {renderPane(right, rightLabel, false)}
    </div>
  );
}

/** Normalised ratio helpers so tests and callers share one vocabulary. */
export function presetToRatio(preset) {
  const map = { '40-60': '40 / 60', '50-50': '50 / 50', '60-40': '60 / 40' };
  return map[preset] || '50 / 50';
}
