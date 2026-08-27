// frontend/src/v3/components/ui/statusConfig.js
// D21.4 — single status vocabulary for the V3 surface, reconciled with the
// authoritative backend state model (backend/domain/partners.py, entity.py,
// issue.py, v3_reports.py).
//
// Every status maps to a human label + tone + icon so the UI never relies on
// colour alone. Unknown statuses fall back to a neutral muted presentation of
// the raw value (never silently dropped).

export const STATUS_TONE = {
  success: 'success',
  warning: 'warning',
  error: 'error',
  info: 'info',
  processing: 'processing',
  muted: 'muted',
};

const STATUSES = {
  // Item statuses (manual-extraction items)
  pending: { label: 'Pending', tone: 'warning', icon: 'clock' },
  extracting: { label: 'Extracting', tone: 'processing', icon: 'loader' },
  extracted: { label: 'Extracted', tone: 'info', icon: 'documents' },
  mapping: { label: 'Mapping', tone: 'processing', icon: 'loader' },
  mapped: { label: 'Mapped', tone: 'info', icon: 'link' },
  validating: { label: 'Validating', tone: 'processing', icon: 'loader' },
  validated: { label: 'Validated', tone: 'info', icon: 'checkCircle' },
  calculating: { label: 'Calculating', tone: 'processing', icon: 'loader' },
  calculated: { label: 'Calculated', tone: 'success', icon: 'calculator' },
  customer_review: { label: 'Customer review', tone: 'warning', icon: 'eye' },
  approved: { label: 'Approved', tone: 'success', icon: 'checkCircle' },
  rejected: { label: 'Rejected', tone: 'error', icon: 'xCircle' },
  qc_approved: { label: 'QC approved', tone: 'success', icon: 'checkCircle' },
  qc_rejected: { label: 'QC rejected', tone: 'error', icon: 'xCircle' },
  failed: { label: 'Failed', tone: 'error', icon: 'xCircle' },

  // Batch statuses
  open: { label: 'Open', tone: 'info', icon: 'folder' },
  in_progress: { label: 'In progress', tone: 'processing', icon: 'loader' },
  qc_in_progress: { label: 'QC in progress', tone: 'processing', icon: 'loader' },
  qc_passed: { label: 'QC passed', tone: 'success', icon: 'checkCircle' },
  completed: { label: 'Completed', tone: 'success', icon: 'checkCircle' },
  cancelled: { label: 'Cancelled', tone: 'warning', icon: 'xCircle' },

  // Issue statuses (ADR-V3-009)
  on_hold: { label: 'On hold', tone: 'warning', icon: 'pause' },
  escalated: { label: 'Escalated', tone: 'error', icon: 'alert' },
  resolved: { label: 'Resolved', tone: 'success', icon: 'checkCircle' },
  closed: { label: 'Closed', tone: 'success', icon: 'checkCircle' },

  // Report statuses
  generating: { label: 'Generating', tone: 'processing', icon: 'loader' },

  // Entity lifecycle
  active: { label: 'Active', tone: 'success', icon: 'checkCircle' },
  remediation: { label: 'Remediation', tone: 'warning', icon: 'alert' },
  suspended: { label: 'Suspended', tone: 'warning', icon: 'pause' },
  terminated: { label: 'Terminated', tone: 'muted', icon: 'xCircle' },

  // Subscription / billing
  trial: { label: 'Trial', tone: 'info', icon: 'clock' },
  past_due: { label: 'Past due', tone: 'error', icon: 'alert' },
  expired: { label: 'Expired', tone: 'muted', icon: 'xCircle' },

  // Factor lifecycle (D9)
  draft: { label: 'Draft', tone: 'warning', icon: 'clock' },
  inactive: { label: 'Inactive', tone: 'muted', icon: 'pause' },

  // Evidence completeness (D33)
  COMPLETE: { label: 'Complete', tone: 'evidence-complete', icon: 'checkCircle' },
  PARTIAL: { label: 'Partial', tone: 'evidence-partial', icon: 'alert' },
  UNAVAILABLE: { label: 'Unavailable', tone: 'evidence-unavailable', icon: 'xCircle' },

  // Human-facing review concepts
  needs_review: { label: 'Needs review', tone: 'warning', icon: 'eye' },
  correction_required: { label: 'Correction required', tone: 'warning', icon: 'alert' },
};

/** Resolve a backend status to {label, tone, icon}; unknown → muted raw. */
export function getStatus(status) {
  if (!status) return { label: '—', tone: 'muted', icon: 'info' };
  const key = String(status).toLowerCase();
  return STATUSES[key] || { label: status, tone: 'muted', icon: 'info' };
}

export { STATUSES };
