// frontend/src/v3/components/ui/Dialog.jsx
// D21 — modal dialog with focus trap, Escape-to-close and focus restore
// (D21.9). ConfirmationDialog standardises approve/reject/delete confirmations.
import React from 'react';
import Button from './Button';
import Icon from './Icon';
import { useFocusTrap } from './hooks';
import './ui.css';

export default function Dialog({ open, onClose, title, children, actions, maxWidth = 560 }) {
  const ref = useFocusTrap(open, { onEscape: onClose });

  if (!open) return null;

  return (
    <div
      className="ct-dialog-backdrop"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="presentation"
    >
      <div
        ref={ref}
        className="ct-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ct-dialog-title"
        style={{ maxWidth }}
      >
        {title && <h2 className="ct-dialog__title" id="ct-dialog-title">{title}</h2>}
        <button type="button" className="ct-dialog__close" onClick={onClose} aria-label="Close dialog">
          <Icon name="x" size={18} aria-hidden="true" />
        </button>
        <div>{children}</div>
        {actions && <div className="ct-dialog__actions">{actions}</div>}
      </div>
    </div>
  );
}

export function ConfirmationDialog({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  tone = 'primary',
  busy = false,
  confirmIcon,
}) {
  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onClose}
      title={title}
      actions={
        <>
          <Button variant="secondary" onClick={onClose} disabled={busy}>{cancelLabel}</Button>
          <Button variant={tone === 'danger' ? 'danger' : 'approve'} onClick={onConfirm} icon={confirmIcon} loading={busy}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p style={{ margin: 0 }}>{message}</p>
    </Dialog>
  );
}
