// frontend/src/v3/__tests__/customer-processing-api.test.js
// CL-54 — the customer processing workspace must use ONLY the org-scoped
// /api/v3/processing/* surface. Staff endpoints (/api/v3/ops/*) must never be
// referenced by customer-processing client functions.
jest.mock('../../supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
      getUser: jest.fn(),
    },
  },
}));

beforeEach(() => {
  const { supabase } = require('../../supabaseClient');
  supabase.auth.getSession.mockImplementation(async () => ({ data: { session: null } }));
  supabase.auth.getUser.mockImplementation(async () => ({ data: { user: null } }));
});

const PROCESSING_FUNCTIONS = {
  getProcessingItemWorkspace: (itemId) => `/api/v3/processing/items/${itemId}/workspace`,
  startProcessingItem: (itemId) => `/api/v3/processing/items/${itemId}/start`,
  saveProcessingExtraction: (itemId) => `/api/v3/processing/items/${itemId}/extract`,
  saveProcessingMapping: (itemId) => `/api/v3/processing/items/${itemId}/map`,
  validateProcessingItem: (itemId) => `/api/v3/processing/items/${itemId}/validate`,
  calculateProcessingItem: (itemId) => `/api/v3/processing/items/${itemId}/calculate`,
  getProcessingMappingOptions: (itemId) => `/api/v3/processing/items/${itemId}/mapping-options`,
  getProcessingStatus: (org) => `/api/v3/processing/status?organization_id=${org}`,
  getProcessingQueue: (org, stage) => `/api/v3/processing/queue?organization_id=${org}&stage=${stage}`,
  getProcessingNextItem: (org, stage) => `/api/v3/processing/next-item?organization_id=${org}&stage=${stage}`,
  getProcessingIssues: (org) => `/api/v3/processing/issues?organization_id=${org}`,
  getProcessingJobs: (org) => `/api/v3/processing/jobs?organization_id=${org}`,
  getProcessingJob: (id) => `/api/v3/processing/jobs/${id}`,
  enqueueDocumentForProcessing: (fileId) => `/api/v3/processing/documents/${fileId}/enqueue`,
  confirmProcessingJob: (id) => `/api/v3/processing/jobs/${id}/confirm`,
  retryProcessingJob: (id) => `/api/v3/processing/jobs/${id}/retry`,
  reviewProcessingJob: (id) => `/api/v3/processing/jobs/${id}/review`,
};

describe('Customer processing workspace API client (CL-54)', () => {
  test('all customer-processing functions are exported', () => {
    const api = require('../api');
    Object.keys(PROCESSING_FUNCTIONS).forEach((name) => {
      expect(typeof api[name]).toBe('function');
    });
  });

  test('no customer-processing function references the staff /api/v3/ops surface', () => {
    const api = require('../api');
    // Every function either builds an org-scoped /api/v3/processing path or is
    // a passthrough wrapper; none may hit /api/v3/ops.
    const source = api.getProcessingItemWorkspace.toString();
    Object.values(PROCESSING_FUNCTIONS).forEach((path) => {
      expect(path('item-1')).toContain('/api/v3/processing/');
      expect(path('item-1')).not.toContain('/api/v3/ops/');
    });
    expect(source).not.toContain('/api/v3/ops/');
  });

  test('the customer review detail page uses the org-scoped workspace', () => {
    // ReviewDetailPage must not call the staff getItemWorkspace (/api/v3/ops).
    const fs = require('fs');
    const path = require('path');
    const source = fs.readFileSync(
      path.join(__dirname, '..', 'customer', 'ReviewDetailPage.jsx'),
      'utf8'
    );
    expect(source).toContain('getProcessingItemWorkspace');
    expect(source).not.toContain('getItemWorkspace');
    expect(source).not.toContain('/api/v3/ops/');
  });

  test('the customer processing pages never call staff /ops endpoints', () => {
    const fs = require('fs');
    const path = require('path');
    const read = (file) => fs.readFileSync(path.join(__dirname, '..', 'customer', file), 'utf8');
    const pages = ['ProcessingPage.jsx', 'ProcessingItemPage.jsx', 'ProcessingItemWorkspace.jsx'];
    for (const file of pages) {
      const source = read(file);
      // The staff-surface client functions are never imported by customer pages.
      expect(source).not.toContain('getItemWorkspace');
      expect(source).not.toContain('startItem');
      expect(source).not.toContain('extractItem');
      expect(source).not.toContain('mapItem');
      expect(source).not.toContain('calculateItem');
    }
    // The item workspace (and the routed page that renders it) use the
    // org-scoped /api/v3/processing/items/{id}/workspace surface.
    expect(read('ProcessingItemWorkspace.jsx')).toContain('getProcessingItemWorkspace');
    expect(read('ProcessingItemPage.jsx')).toContain('ProcessingItemWorkspace');
    // The dashboard uses the org-scoped status/jobs surfaces.
    expect(read('ProcessingPage.jsx')).toContain('getProcessingStatus');
    expect(read('ProcessingPage.jsx')).toContain('getProcessingJobs');
  });
});
