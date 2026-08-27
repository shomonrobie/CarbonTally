// frontend/src/v3/__tests__/review-api.test.js
// API-client surface tests for the Phase 2 additions: customer review (D5),
// custom factors (D9), vehicles (D17) and retention settings (N3).
jest.mock('../../supabaseClient', () => ({
  supabase: { auth: { getSession: async () => ({ data: { session: null } }) } },
}));

import {
  getCustomerReviewQueue,
  getItemWorkspace,
  submitCustomerReview,
  resolveV3Membership,
  listCustomerFactors,
  createCustomerFactor,
  approveCustomerFactor,
  deactivateCustomerFactor,
  listVehicles,
  createVehicle,
  removeVehicle,
  getRetentionSettings,
  updateRetentionSettings,
} from '../api';

describe('Phase 2 API client surface', () => {
  const endpointFunctions = [
    ['getCustomerReviewQueue', getCustomerReviewQueue],
    ['getItemWorkspace', getItemWorkspace],
    ['submitCustomerReview', submitCustomerReview],
    ['resolveV3Membership', resolveV3Membership],
    ['listCustomerFactors', listCustomerFactors],
    ['createCustomerFactor', createCustomerFactor],
    ['approveCustomerFactor', approveCustomerFactor],
    ['deactivateCustomerFactor', deactivateCustomerFactor],
    ['listVehicles', listVehicles],
    ['createVehicle', createVehicle],
    ['removeVehicle', removeVehicle],
    ['getRetentionSettings', getRetentionSettings],
    ['updateRetentionSettings', updateRetentionSettings],
  ];

  test.each(endpointFunctions)('%s is exported and callable', (_name, fn) => {
    expect(typeof fn).toBe('function');
  });

  test('submitCustomerReview is a POST to the approver-gated endpoint', () => {
    // The function is exported and callable; the endpoint path is fixed to the
    // D5 approver-gated customer-review surface.
    expect(typeof submitCustomerReview).toBe('function');
    expect(submitCustomerReview.toString()).toContain('/api/v3/processing/items/');
    expect(submitCustomerReview.toString()).toContain('/customer-review');
    expect(submitCustomerReview.toString()).toContain('method: \'POST\'');
  });

  test('resolveV3Membership returns null without a session', async () => {
    // getV3Token returns null when there is no session, so the resolver bails.
    expect(await resolveV3Membership()).toBeNull();
  });
});
