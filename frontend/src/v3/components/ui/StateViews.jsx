// frontend/src/v3/components/ui/StateViews.jsx
// D29/F3 — shared LOADING / ERROR / EMPTY state primitives. Bounded retryable
// errors, informative empty states and loading spinners for every V3 surface.
import React from 'react';
import Button from './Button';
import Icon from './Icon';
import './ui.css';

export function LoadingState({ label = 'Loading…', inline = false }) {
  return (
    <div className={`ct-loading${inline ? ' ct-state--inline' : ''}`} role="status">
      <div className="ct-spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry, title = 'Something went wrong', inline }) {
  return (
    <div className={`ct-state${inline ? ' ct-state--inline' : ''}`}>
      <div className="ct-state__icon" aria-hidden="true"><Icon name="alert" size={30} /></div>
      <div className="ct-state__title">{title}</div>
      <div className="ct-state__body">{message || 'Please try again.'}</div>
      {onRetry && (
        <div className="ct-state__actions">
          <Button variant="primary" icon="refresh" onClick={onRetry}>Retry</Button>
        </div>
      )}
    </div>
  );
}

export function EmptyState({ children, icon = 'folder', title, action }) {
  return (
    <div className="ct-state">
      <div className="ct-state__icon" aria-hidden="true"><Icon name={icon} size={30} /></div>
      {title && <div className="ct-state__title">{title}</div>}
      <div className="ct-state__body">{children}</div>
      {action && <div className="ct-state__actions">{action}</div>}
    </div>
  );
}

export function PermissionState({ message = 'You do not have permission to view this content.' }) {
  return (
    <div className="ct-state" role="alert">
      <div className="ct-state__icon" aria-hidden="true"><Icon name="lock" size={30} /></div>
      <div className="ct-state__title">Access denied</div>
      <div className="ct-state__body">{message}</div>
    </div>
  );
}
