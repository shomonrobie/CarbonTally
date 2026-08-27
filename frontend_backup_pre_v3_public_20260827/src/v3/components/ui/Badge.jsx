// frontend/src/v3/components/ui/Badge.jsx
// D21.4 — Badge primitive. Status must never be communicated by colour alone,
// so Badge always carries a text label (children) and optionally an icon.
import React from 'react';
import Icon from './Icon';
import './ui.css';

const TONE_CLASS = {
  success: 'ct-badge--success',
  warning: 'ct-badge--warning',
  error: 'ct-badge--error',
  info: 'ct-badge--info',
  processing: 'ct-badge--processing',
  muted: 'ct-badge--muted',
  primary: 'ct-badge--primary',
  'evidence-complete': 'ct-badge--evidence-complete',
  'evidence-partial': 'ct-badge--evidence-partial',
  'evidence-unavailable': 'ct-badge--evidence-unavailable',
};

export default function Badge({ tone = 'muted', icon, children, className = '', ...rest }) {
  return (
    <span className={`ct-badge ${TONE_CLASS[tone] || ''} ${className}`.trim()} {...rest}>
      {icon && <Icon name={icon} size={12} aria-hidden="true" />}
      {children}
    </span>
  );
}
