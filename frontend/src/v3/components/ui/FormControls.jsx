// frontend/src/v3/components/ui/FormControls.jsx
// D21.6 — accessible form field primitives: bound labels, required markers,
// inline errors, helper text, read-only and disabled states.
import React, { useRef } from 'react';
import { v4 as uuid } from './uuidFallback';
import './ui.css';

/** Stable per-instance id generator (never called conditionally). */
function useFieldId(prefix) {
  const ref = useRef(null);
  if (ref.current === null) {
    ref.current = `${prefix}-${uuid()}`;
  }
  return ref.current;
}

/**
 * Shared field chrome. `label` is always associated with the control via
 * htmlFor/id so screen readers announce it (D21.9).
 */
function FieldShell({ label, htmlFor, required, optional, hint, error, readOnly, children }) {
  return (
    <div className={`ct-field${readOnly ? ' ct-field--readonly' : ''}`}>
      {label && (
        <label className="ct-field__label" htmlFor={htmlFor}>
          {label}
          {required && <span className="ct-field__required" aria-hidden="true"> *</span>}
          {optional && <span className="ct-field__optional"> (optional)</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="ct-field__hint">{hint}</p>}
      {error && (
        <p className="ct-field__error" id={`${htmlFor}-error`} role="alert">{error}</p>
      )}
    </div>
  );
}

export function Field({ label, required, optional, hint, error, readOnly, children, id }) {
  return (
    <FieldShell
      label={label}
      htmlFor={id}
      required={required}
      optional={optional}
      hint={hint}
      error={error}
      readOnly={readOnly}
    >
      {React.cloneElement(children, {
        id,
        'aria-invalid': error ? 'true' : undefined,
        'aria-describedby': error ? `${id}-error` : hint ? `${id}-hint` : undefined,
        readOnly,
      })}
    </FieldShell>
  );
}

export function TextInput({ label, required, optional, hint, error, readOnly, ...rest }) {
  const generatedId = useFieldId('ct-input');
  const id = rest.id || generatedId;
  return (
    <Field label={label} id={id} required={required} optional={optional} hint={hint} error={error} readOnly={readOnly}>
      <input type="text" className="ct-field__control" id={id} {...rest} />
    </Field>
  );
}

export function SelectInput({ label, required, optional, hint, error, readOnly, children, ...rest }) {
  const generatedId = useFieldId('ct-select');
  const id = rest.id || generatedId;
  return (
    <Field label={label} id={id} required={required} optional={optional} hint={hint} error={error} readOnly={readOnly}>
      <select className="ct-field__control" id={id} {...rest}>{children}</select>
    </Field>
  );
}

export function TextArea({ label, required, optional, hint, error, readOnly, rows = 3, ...rest }) {
  const generatedId = useFieldId('ct-textarea');
  const id = rest.id || generatedId;
  return (
    <Field label={label} id={id} required={required} optional={optional} hint={hint} error={error} readOnly={readOnly}>
      <textarea className="ct-field__control" id={id} rows={rows} {...rest} />
    </Field>
  );
}

export function CheckboxField({ label, hint, error, ...rest }) {
  const generatedId = useFieldId('ct-check');
  const id = rest.id || generatedId;
  return (
    <div className="ct-field">
      <div className="ct-field__row">
        <input type="checkbox" id={id} {...rest} />
        <label htmlFor={id}>{label}</label>
      </div>
      {hint && !error && <p className="ct-field__hint">{hint}</p>}
      {error && <p className="ct-field__error" role="alert">{error}</p>}
    </div>
  );
}
