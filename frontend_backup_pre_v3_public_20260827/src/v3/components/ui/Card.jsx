// frontend/src/v3/components/ui/Card.jsx
// D21 — Card and StatCard primitives.
import React from 'react';
import './ui.css';

export function Card({ title, actions, children, className = '', ...rest }) {
  return (
    <section className={`ct-card ${className}`.trim()} {...rest}>
      {(title || actions) && (
        <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
          {title && <h2 className="ct-card__title" style={{ margin: 0 }}>{title}</h2>}
          {actions && <div>{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function StatCard({ label, value, to, className = '', ...rest }) {
  const Tag = to ? 'a' : 'div';
  return (
    <Tag href={to} className={`ct-stat-card ${className}`.trim()} {...rest}>
      <div className="ct-stat-card__label">{label}</div>
      <div className="ct-stat-card__value">{value}</div>
    </Tag>
  );
}
