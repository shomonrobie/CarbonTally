// frontend/src/v3/components/workbench/ConfidenceBadge.jsx
// D16/D19 — confidence indicator for AI-suggested extraction fields.
// Confidence is never an authorisation or calculation authority: it is a
// display hint that the value needs human confirmation before it becomes data.
import React from 'react';

function level(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
  const n = Number(value);
  if (n >= 0.8) return { key: 'high', label: 'High confidence' };
  if (n >= 0.5) return { key: 'medium', label: 'Medium confidence' };
  return { key: 'low', label: 'Low confidence — verify' };
}

export default function ConfidenceBadge({ value, field }) {
  const lvl = level(value);
  if (!lvl) return null;
  const pct = `${Math.round(Number(value) * 100)}%`;
  return (
    <span
      className={`ct-confidence ct-confidence--${lvl.key}`}
      title={`${lvl.label}${field ? ` — ${field}` : ''}`}
    >
      {pct} {lvl.label}
    </span>
  );
}
