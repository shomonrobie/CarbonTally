// frontend/src/v3/components/ui/Alert.jsx
// D21 — Alert primitive (info / success / warning / error). Uses role="alert"
// for errors and aria-live regions so screen readers announce state changes.
import React from 'react';
import Icon from './Icon';
import './ui.css';

const TONE_CONFIG = {
  info: { className: 'ct-alert--info', icon: 'info', defaultTitle: 'Note' },
  success: { className: 'ct-alert--success', icon: 'checkCircle', defaultTitle: 'Success' },
  warning: { className: 'ct-alert--warning', icon: 'alert', defaultTitle: 'Attention needed' },
  error: { className: 'ct-alert--error', icon: 'xCircle', defaultTitle: 'Something went wrong' },
};

export default function Alert({ tone = 'info', title, children, className = '', ...rest }) {
  const config = TONE_CONFIG[tone] || TONE_CONFIG.info;
  const role = tone === 'error' ? 'alert' : 'status';
  return (
    <div className={`ct-alert ${config.className} ${className}`.trim()} role={role} {...rest}>
      <span className="ct-alert__icon"><Icon name={config.icon} size={18} aria-hidden="true" /></span>
      <div className="ct-alert__body">
        {title && <div className="ct-alert__title">{title}</div>}
        <div>{children}</div>
      </div>
    </div>
  );
}
