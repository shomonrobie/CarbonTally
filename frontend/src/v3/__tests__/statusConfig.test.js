// frontend/src/v3/__tests__/statusConfig.test.js
// D21.4 — the shared status vocabulary must cover every backend state from the
// authoritative state model (backend/domain/partners.py, entity.py, issue.py,
// v3_reports.py) and never rely on colour alone (always label + tone + icon).
import { getStatus, STATUSES } from '../components/ui/statusConfig';

describe('V3 status vocabulary (D21.4)', () => {
  const backendStatuses = [
    // ITEM_STATUSES
    'pending', 'extracting', 'extracted', 'mapping', 'mapped', 'validating',
    'validated', 'calculating', 'calculated', 'customer_review', 'approved',
    'rejected', 'qc_approved', 'qc_rejected', 'failed',
    // BATCH_STATUSES
    'open', 'in_progress', 'qc_in_progress', 'qc_passed', 'completed', 'cancelled',
    // ISSUE_STATUSES
    'on_hold', 'escalated', 'resolved', 'closed',
    // REPORT_STATUSES
    'generating',
    // ENTITY_STATUSES
    'active', 'remediation', 'suspended', 'terminated',
  ];

  test.each(backendStatuses)('maps backend status %s to a labelled presentation', (status) => {
    const config = getStatus(status);
    expect(typeof config.label).toBe('string');
    expect(config.label.length).toBeGreaterThan(0);
    expect(typeof config.tone).toBe('string');
    expect(typeof config.icon).toBe('string');
    expect(config.icon.length).toBeGreaterThan(0);
  });

  test('maps customer_review to a warning "Customer review" state', () => {
    const config = getStatus('customer_review');
    expect(config.label).toBe('Customer review');
    expect(config.tone).toBe('warning');
  });

  test('maps calculated to a success state (never conflated with approved)', () => {
    const calculated = getStatus('calculated');
    const approved = getStatus('approved');
    expect(calculated.label).toBe('Calculated');
    expect(approved.label).toBe('Approved');
    expect(calculated.label).not.toBe(approved.label);
  });

  test('unknown status falls back to a muted raw presentation', () => {
    const config = getStatus('made_up_status');
    expect(config.tone).toBe('muted');
    expect(config.label).toBe('made_up_status');
  });

  test('null/undefined status renders an em-dash', () => {
    expect(getStatus(null).label).toBe('—');
    expect(getStatus(undefined).label).toBe('—');
  });

  test('every registered status has a non-empty label', () => {
    Object.values(STATUSES).forEach((config) => {
      expect(typeof config.label).toBe('string');
      expect(config.label.length).toBeGreaterThan(0);
    });
  });
});
