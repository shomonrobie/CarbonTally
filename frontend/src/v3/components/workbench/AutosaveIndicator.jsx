// frontend/src/v3/components/workbench/AutosaveIndicator.jsx
// D19 — autosave state indicator. Announces state changes to assistive
// technology via an aria-live region.
import React from 'react';
import Icon from '../ui/Icon';

const STATE = {
  idle: { label: 'Not saved yet', className: '' },
  saving: { label: 'Saving…', className: 'ct-wb-autosave--saving', icon: 'loader' },
  saved: { label: 'Saved', className: 'ct-wb-autosave--saved', icon: 'checkCircle' },
  error: { label: 'Save failed', className: 'ct-wb-autosave--error', icon: 'alert' },
};

export default function AutosaveIndicator({ state = 'idle', lastSavedAt }) {
  const config = STATE[state] || STATE.idle;
  return (
    <span className={`ct-wb-autosave ${config.className}`.trim()} role="status" aria-live="polite">
      <Icon name={config.icon || 'save'} size={12} aria-hidden="true" />
      {config.label}
      {lastSavedAt && state === 'saved' ? ` at ${lastSavedAt}` : ''}
    </span>
  );
}
