// frontend/src/v3/components/ui/StatusBadge.jsx
// D21.4 — status indicator derived from the shared status vocabulary.
// Always renders text + icon + colour (never colour alone).
import React from 'react';
import { getStatus } from './statusConfig';
import Badge from './Badge';

export default function StatusBadge({ status, className = '', ...rest }) {
  const config = getStatus(status);
  return (
    <Badge tone={config.tone} icon={config.icon} className={className} {...rest}>
      {config.label}
    </Badge>
  );
}
