// frontend/src/v3/components/ui/Button.jsx
// D21.5 — Button primitive (primary / secondary / ghost / danger / approve /
// reject), sizes, loading and icon support. Renders a <button> or <a>.
import React from 'react';
import Icon from './Icon';
import './ui.css';

const VARIANT_CLASS = {
  primary: 'ct-btn--primary',
  secondary: '',
  ghost: 'ct-btn--ghost',
  danger: 'ct-btn--danger',
  approve: 'ct-btn--approve',
  reject: 'ct-btn--reject',
};

const SIZE_CLASS = { sm: 'ct-btn--sm', md: '', lg: 'ct-btn--lg' };

export default function Button({
  variant = 'secondary',
  size = 'md',
  icon,
  loading = false,
  block = false,
  className = '',
  children,
  disabled,
  href,
  type = 'button',
  ...rest
}) {
  const classes = [
    'ct-btn',
    VARIANT_CLASS[variant] || '',
    SIZE_CLASS[size] || '',
    block ? 'ct-btn--block' : '',
    icon && !children ? 'ct-btn--icon' : '',
    className,
  ].filter(Boolean).join(' ');

  const content = (
    <>
      {loading && <span className="ct-btn-spinner" aria-hidden="true" />}
      {!loading && icon && <Icon name={icon} size={16} aria-hidden="true" />}
      {children}
    </>
  );

  const ariaProps = { 'aria-busy': loading || undefined, ...rest };

  if (href) {
    return (
      <a href={href} className={classes} aria-disabled={disabled || loading} {...ariaProps}>
        {content}
      </a>
    );
  }

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...ariaProps}>
      {content}
    </button>
  );
}
