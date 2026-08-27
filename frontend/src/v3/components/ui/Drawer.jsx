// frontend/src/v3/components/ui/Drawer.jsx
// D20 — drawer / tray primitive used by the responsive shell and workbench
// (tablet tray navigation, mobile source/data switching). Focus-trapped like a
// dialog, closes on Escape or backdrop click.
import React from 'react';
import Icon from './Icon';
import { useFocusTrap } from './hooks';
import './ui.css';

export default function Drawer({ open, onClose, title, children, side = 'right' }) {
  const ref = useFocusTrap(open, { onEscape: onClose });

  if (!open) return null;

  return (
    <>
      <div className="ct-drawer-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }} aria-hidden="true" />
      <div
        ref={ref}
        className={`ct-drawer ct-drawer--${side}`}
        role="dialog"
        aria-modal="true"
        aria-label={title || 'Panel'}
      >
        <div className="ct-drawer__header">
          {title && <h2 className="ct-drawer__title">{title}</h2>}
          <button type="button" onClick={onClose} aria-label="Close panel" className="ct-dialog__close" style={{ position: 'static' }}>
            <Icon name="x" size={18} aria-hidden="true" />
          </button>
        </div>
        <div className="ct-drawer__body">{children}</div>
      </div>
    </>
  );
}
